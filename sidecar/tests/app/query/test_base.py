import os
from pathlib import Path
from unittest import mock
from uuid import uuid4

import pytest

from sidecar.app.query.base import MaxQueriesRunningError, Query, QueryManager
from sidecar.app.query.status import Status


@pytest.fixture(autouse=True)
def mock_settings_env_vars(tmp_path):
    env_vars = {
        "ROLE": "0",
        "ROOT_PATH": str(tmp_path),
        "CONFIG_PATH": str(Path("local_dev/config")),
        "NETWORK_CONFIG_PATH": str(Path("local_dev/config") / Path("network.toml")),
        "HELPER_PORT": str(17440),
    }
    with mock.patch.dict(os.environ, env_vars):
        yield


def test_query_files():
    query = Query(str(uuid4()))
    assert not query.status_file_path.exists()
    assert query.log_file_path.exists()
    query.status = Status.STARTING
    assert query.status_file_path.exists()


def test_query_started():
    for status in Status:
        query = Query(str(uuid4()))
        query.status = status
        if status < Status.STARTING:
            assert not query.started
        else:
            assert query.started


def test_query_finished():
    for status in Status:
        query = Query(str(uuid4()))
        query.status = status
        if status < Status.COMPLETE:
            assert not query.finished
        else:
            assert query.finished


@mock.patch("time.time", return_value=3.14)
def test_query_status_event_json(mock_time):
    query = Query(str(uuid4()))
    query.status = Status.STARTING
    # in Query.status setter, we do two checks, which generate new UNKNOWN events
    # within StatusHistory.add, we do two checks which also generate new UNKNOWN events
    # finally, it's called for the actual new status setting
    assert mock_time.call_count == 5
    assert query.status_event_json == {"status": "STARTING", "start_time": 3.14}


def test_query_running():
    for status in Status:
        query = Query(str(uuid4()))
        query.status = status
        if Status.STARTING <= status < Status.COMPLETE:
            assert query.running
        else:
            assert not query.running


def test_query_manager():
    query_manager = QueryManager(max_parallel_queries=1)
    query = Query(str(uuid4()))
    assert query_manager.get_from_query_id(Query, query.query_id) is None
    query.status = Status.STARTING
    assert query_manager.get_from_query_id(Query, query.query_id) == query


def test_query_manager_capacity_available():
    query_manager = QueryManager(max_parallel_queries=1)
    assert query_manager.capacity_available
    query = Query(str(uuid4()))
    query_manager.running_queries[query.query_id] = query
    assert not query_manager.capacity_available
    del query_manager.running_queries[query.query_id]
    assert query_manager.capacity_available


def test_query_manger_run_query():
    query_manager = QueryManager(max_parallel_queries=1)
    query = Query(str(uuid4()))

    def fake_start():
        assert query.query_id in query_manager.running_queries

    with mock.patch(
        "sidecar.app.query.base.Query.start", side_effect=fake_start
    ) as mock_start:
        query_manager.run_query(query)
        mock_start.assert_called_once()

    assert query.query_id not in query_manager.running_queries


def test_query_manger_run_query_at_capacity():
    query_manager = QueryManager(max_parallel_queries=1)
    query = Query(str(uuid4()))
    query2 = Query(str(uuid4()))

    def fake_start():
        with pytest.raises(MaxQueriesRunningError):
            query_manager.run_query(query2)

    with mock.patch(
        "sidecar.app.query.base.Query.start", side_effect=fake_start
    ) as mock_start:
        query_manager.run_query(query)
        mock_start.assert_called_once()


def test_query_manger_run_query_exception():
    query_manager = QueryManager(max_parallel_queries=1)
    query = Query(str(uuid4()))

    def mock_exception():
        raise Exception

    with mock.patch(
        "sidecar.app.query.base.Query.start", side_effect=mock_exception
    ) as mock_start:
        with pytest.raises(Exception):
            query_manager.run_query(query)

        mock_start.assert_called_once()

    assert query.query_id not in query_manager.running_queries
    assert query_manager.capacity_available
