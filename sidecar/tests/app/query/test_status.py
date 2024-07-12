import time
from pathlib import Path

import loguru
import pytest

from sidecar.app.query.status import Status, StatusChangeEvent, StatusHistory


@pytest.fixture(name="status_history_fixture")
def _status_history_fixture(tmp_path):
    status_history = StatusHistory(
        file_path=tmp_path / Path("status"),
        logger=loguru.logger,
    )

    return status_history


@pytest.fixture(name="full_status_history_fixture")
def _full_status_history_fixture(status_history_fixture):
    status_events = [
        (Status.STARTING, 1.0),
        (Status.COMPILING, 2.0),
        (Status.WAITING_TO_START, 3.0),
        (Status.IN_PROGRESS, 4.0),
        (Status.COMPLETE, 5.0),
    ]

    for status, timestamp in status_events:
        status_history_fixture.add(status, timestamp)

    return status_history_fixture


def test_status_history_add(status_history_fixture):
    now = time.time()
    status_history_fixture.add(Status.COMPILING, now)
    assert status_history_fixture.current_status_event == StatusChangeEvent(
        Status.COMPILING, now
    )
    now = time.time()
    status_history_fixture.add(Status.IN_PROGRESS, now)
    assert status_history_fixture.current_status_event == StatusChangeEvent(
        Status.IN_PROGRESS, now
    )


def test_status_history_add_write_to_file(status_history_fixture):
    status_history_fixture.add(Status.COMPILING, 1.0)
    status_history_fixture.add(Status.IN_PROGRESS, 2.0)
    with status_history_fixture.file_path.open("r", encoding="utf-8") as f:
        assert f.readline() == "COMPILING,1.0\n"
        assert f.readline() == "IN_PROGRESS,2.0\n"


def test_status_history_add_load_from_file(tmp_path, full_status_history_fixture):
    status_history = StatusHistory(
        file_path=tmp_path / Path("status"),
        logger=loguru.logger,
    )
    assert status_history == full_status_history_fixture


def test_status_history_cannot_add_when_locked(full_status_history_fixture):
    with pytest.raises(AssertionError):
        now = time.time()
        full_status_history_fixture.add(Status.KILLED, now)


def test_status_history_cannot_add_lower_status(status_history_fixture):
    now = time.time()
    status_history_fixture.add(Status.IN_PROGRESS, now)
    assert status_history_fixture.current_status_event == StatusChangeEvent(
        Status.IN_PROGRESS, now
    )
    with pytest.raises(AssertionError):
        now = time.time()
        status_history_fixture.add(Status.COMPILING, now)


def test_status_history_current_status_event(full_status_history_fixture):
    assert full_status_history_fixture.current_status_event == StatusChangeEvent(
        Status.COMPLETE, 5.0
    )


def test_status_history_current_status(full_status_history_fixture):
    assert full_status_history_fixture.current_status == Status.COMPLETE


def test_status_history_status_event_json(
    status_history_fixture,
):
    now = time.time()
    status_history_fixture.add(Status.COMPILING, now)
    assert status_history_fixture.status_event_json == {
        "status": Status.COMPILING.name,
        "start_time": now,
    }

    now = time.time()
    status_history_fixture.add(Status.IN_PROGRESS, now)
    assert status_history_fixture.status_event_json == {
        "status": Status.IN_PROGRESS.name,
        "start_time": now,
    }

    now2 = time.time()
    status_history_fixture.add(Status.COMPLETE, now2)
    assert status_history_fixture.status_event_json == {
        "status": Status.COMPLETE.name,
        "start_time": now,
        "end_time": now2,
    }
