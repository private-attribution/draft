import os
from pathlib import Path
from unittest import mock
from uuid import uuid4

import pytest

from sidecar.app.query.base import Query, queries
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


def test_queries_storage():
    query_id = str(uuid4())
    query = Query(query_id)
    assert queries[query_id] == query
    assert Query.get_from_query_id(query_id) == query
    assert Query.get_from_query_id("foo") is None
    assert "foo" not in queries


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
