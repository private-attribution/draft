from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import NamedTuple, Optional

import loguru


class Status(IntEnum):
    UNKNOWN = auto()
    NOT_FOUND = auto()
    STARTING = auto()
    COMPILING = auto()
    WAITING_TO_START = auto()
    IN_PROGRESS = auto()
    COMPLETE = auto()
    KILLED = auto()
    CRASHED = auto()

    @classmethod
    def from_json(cls, response: dict[str, str]):
        status_str = response.get("status", "")
        try:
            return cls[status_str]
        except ValueError:
            return cls.UNKNOWN


StatusChangeEvent = NamedTuple(
    "StatusChangeEvent", [("status", Status), ("timestamp", float)]
)


@dataclass
class StatusHistory:
    file_path: Path = field(init=True, repr=False)
    logger: loguru.Logger = field(init=True, repr=False, compare=False)
    _status_history: list[StatusChangeEvent] = field(
        init=False, default_factory=list, repr=True
    )

    def __post_init__(self):
        if self.file_path.exists():
            self.logger.debug(f"Loading status history from file {self.file_path}")
            with self.file_path.open("r", encoding="utf8") as f:
                for line in f:
                    status_str, timestamp = line.split(",")
                    self._status_history.append(
                        StatusChangeEvent(
                            status=Status[status_str], timestamp=float(timestamp)
                        )
                    )

    @property
    def locking_status(self):
        """Cannot add to history after this or higher status is reached"""
        return Status.COMPLETE

    def add(self, status: Status, timestamp: Optional[float] = None):
        if timestamp is None:
            timestamp = time.time()
        assert status > self.current_status
        assert self.current_status < self.locking_status
        self._status_history.append(
            StatusChangeEvent(status=status, timestamp=timestamp)
        )
        with self.file_path.open("a", encoding="utf8") as f:
            self.logger.debug(f"updating status: {status=}")
            f.write(f"{status.name},{timestamp}\n")

    @property
    def current_status_event(self):
        if not self._status_history:
            return StatusChangeEvent(status=Status.UNKNOWN, timestamp=time.time())
        return self._status_history[-1]

    @property
    def current_status(self):
        return self.current_status_event.status

    @property
    def status_event_json(self):
        status_event = {
            "status": self.current_status_event.status.name,
            "start_time": self.current_status_event.timestamp,
        }
        if self.current_status >= Status.COMPLETE and len(self._status_history) >= 2:
            status_event["start_time"] = self._status_history[-2].timestamp
            status_event["end_time"] = self.current_status_event.timestamp
        return status_event
