import os
from pathlib import Path
from unittest import mock

import pytest

from sidecar.app.query.base import Query, queries


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


@pytest.fixture(name="query_fixture")
def _query_fixture():
    return Query("foo")


def test_queries_storage(query_fixture):
    assert queries["foo"] == query_fixture
