from unittest import mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sidecar.app.helpers import Role
from sidecar.app.main import app
from sidecar.app.query.status import Status
from sidecar.app.routes.start import IncorrectRoleError, Query
from sidecar.app.settings import get_settings

client = TestClient(app)


@pytest.fixture(name="mock_role")
def _mock_role():
    def __mock_role(role: Role):
        settings = get_settings()
        settings.role = role
        return settings

    return __mock_role


@pytest.fixture(name="running_query")
def _running_query():
    query = Query(str(uuid4()))
    query_manager = app.state.QUERY_MANAGER
    query_manager.running_queries[query.query_id] = query
    query.status = Status.STARTING
    yield query
    del query_manager.running_queries[query.query_id]


def test_capacity_available():
    response = client.get("/start/capacity-available")
    assert response.status_code == 200
    assert response.json() == {"capacity_available": True}


def test_not_capacity_available(running_query):
    assert running_query.query_id in app.state.QUERY_MANAGER.running_queries
    response = client.get("/start/capacity-available")
    assert response.status_code == 200
    assert response.json() == {"capacity_available": False}


def test_running_queries(running_query):
    response = client.get("/start/running-queries")
    assert response.status_code == 200
    assert response.json() == {"running_queries": [running_query.query_id]}


def test_start_ipa_helper(mock_role):
    settings = mock_role(Role.HELPER_1)
    with mock.patch("sidecar.app.routes.start.get_settings", return_value=settings):
        with mock.patch(
            "sidecar.app.query.base.QueryManager.run_query"
        ) as mock_query_manager:
            query_id = str(uuid4())
            response = client.post(
                f"/start/ipa-helper/{query_id}",
                data={
                    "commit_hash": "abcd1234",
                    "gate_type": "compact",
                    "stall_detection": True,
                    "multi_threading": True,
                    "disable_metrics": True,
                },
            )
            assert response.status_code == 200
            mock_query_manager.assert_called_once()


def test_start_ipa_helper_as_coordinator(mock_role):
    settings = mock_role(Role.COORDINATOR)
    with pytest.raises(IncorrectRoleError):
        with mock.patch("sidecar.app.routes.start.get_settings", return_value=settings):
            with mock.patch("sidecar.app.query.base.QueryManager.run_query"):
                query_id = str(uuid4())
                client.post(
                    f"/start/ipa-helper/{query_id}",
                    data={
                        "commit_hash": "abcd1234",
                        "gate_type": "compact",
                        "stall_detection": True,
                        "multi_threading": True,
                        "disable_metrics": True,
                    },
                )


def test_start_ipa_query(mock_role):
    settings = mock_role(Role.COORDINATOR)
    with mock.patch("sidecar.app.routes.start.get_settings", return_value=settings):
        with mock.patch(
            "sidecar.app.query.base.QueryManager.run_query"
        ) as mock_query_manager:
            query_id = str(uuid4())
            response = client.post(
                f"/start/ipa-query/{query_id}",
                data={
                    "commit_hash": "abcd1234",
                    "size": 10,
                    "max_breakdown_key": 16,
                    "max_trigger_value": 10,
                    "per_user_credit_cap": 5,
                },
            )
            assert response.status_code == 200
            mock_query_manager.assert_called_once()


def test_start_ipa_query_as_helper(mock_role):
    settings = mock_role(Role.HELPER_1)
    with pytest.raises(IncorrectRoleError):
        with mock.patch("sidecar.app.routes.start.get_settings", return_value=settings):
            with mock.patch("sidecar.app.query.base.QueryManager.run_query"):
                query_id = str(uuid4())
                client.post(
                    f"/start/ipa-query/{query_id}",
                    data={
                        "commit_hash": "abcd1234",
                        "size": 10,
                        "max_breakdown_key": 16,
                        "max_trigger_value": 10,
                        "per_user_credit_cap": 5,
                    },
                )


def test_get_status_not_found():
    query_id = str(uuid4())
    response = client.get(f"/start/{query_id}/status")
    assert response.status_code == 404


def test_get_status_running(running_query):
    response = client.get(f"/start/{running_query.query_id}/status")
    assert response.status_code == 200
    status_event_json = response.json()
    assert status_event_json["status"] == str(Status.STARTING.name)
    assert "start_time" in status_event_json
    assert "end_time" not in status_event_json


def test_get_status_complete(running_query):
    running_query.status = Status.COMPLETE
    response = client.get(f"/start/{running_query.query_id}/status")
    assert response.status_code == 200
    status_event_json = response.json()
    assert status_event_json["status"] == str(Status.COMPLETE.name)
    assert "start_time" in status_event_json
    assert "end_time" in status_event_json


def test_get_ipa_helper_log_file_not_found():
    query_id = str(uuid4())
    response = client.get(f"/start/{query_id}/log-file")
    assert response.status_code == 404


def test_get_ipa_helper_log_file(running_query):
    test_file_content = "log 1\nlog 2\nlog 3\n"
    running_query.log_file_path.write_text(test_file_content, encoding="utf-8")
    response = client.get(f"/start/{running_query.query_id}/log-file")
    assert response.status_code == 200
    assert response.text.startswith(test_file_content)
