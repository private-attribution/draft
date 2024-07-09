# pylint: disable=R0801
from __future__ import annotations

import time
from collections import namedtuple
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional, TypeVar

import loguru

from ..helpers import Role
from ..logger import logger
from ..settings import settings
from .step import Status, Step

# Dictionary to store queries
queries: dict[str, "Query"] = {}


class QueryExistsError(Exception):
    pass


StatusChangeEvent = namedtuple("StatusChangeEvent", ["status", "timestamp"])


@dataclass
class Query:
    # pylint: disable=too-many-instance-attributes
    query_id: str
    current_step: Optional[Step] = field(init=False, default=None, repr=True)
    start_time: Optional[float] = field(init=False, default=None)
    end_time: Optional[float] = field(init=False, default=None)
    stopped: bool = field(init=False, default=False)
    logger: loguru.Logger = field(init=False, repr=False)
    _logger_id: int = field(init=False, repr=False)
    step_classes: ClassVar[list[type[Step]]] = []
    _log_dir: Path = settings.root_path / Path("logs")
    _status_history: list[StatusChangeEvent] = field(
        init=False, default_factory=list, repr=True
    )
    _status_dir: Path = settings.root_path / Path("status_semaphore")

    def __post_init__(self):
        self.logger = logger.bind(task=self.query_id)
        self._log_dir.mkdir(exist_ok=True)
        self._status_dir.mkdir(exist_ok=True)
        self._logger_id = logger.add(
            self.log_file_path,
            serialize=True,
            filter=lambda record: record["extra"].get("task") == self.query_id,
            enqueue=True,
        )
        self.logger.debug(f"adding new Query {self}.")
        if queries.get(self.query_id) is not None:
            raise QueryExistsError(f"{self.query_id} already exists")
        queries[self.query_id] = self

    @property
    def role(self) -> Role:
        return settings.role

    @property
    def started(self) -> bool:
        return self.start_time is not None

    @property
    def finished(self) -> bool:
        return self.end_time is not None

    @classmethod
    def get_from_query_id(cls, query_id) -> Optional["Query"]:
        query = queries.get(query_id)
        if query:
            return query
        try:
            query = cls(query_id)
        except QueryExistsError as e:
            # avoid race condition on queries
            query = queries.get(query_id)
            if query:
                return query
            raise e
        query.load_history_from_file()
        if query.status == Status.UNKNOWN:
            return None
        return query

    def load_history_from_file(self):
        if self.status_file_path.exists():
            self.logger.debug(
                f"Loading query {self.query_id} status history "
                f"from file {self.status_file_path}"
            )
            with self.status_file_path.open("r") as f:
                for line in f:
                    status_str, timestamp = line.split(",")
                    self._status_history.append(
                        StatusChangeEvent(
                            status=Status[status_str], timestamp=float(timestamp)
                        )
                    )

    @property
    def _last_status_event(self):
        if not self._status_history:
            return StatusChangeEvent(status=Status.UNKNOWN, timestamp=time.time())
        return self._status_history[-1]

    @property
    def status_event_json(self):
        status_event = {
            "status": self._last_status_event.status.name,
            "start_time": self._last_status_event.timestamp,
        }
        if self.status >= Status.COMPLETE and len(self._status_history) >= 2:
            status_event["start_time"] = self._status_history[-2].timestamp
            status_event["end_time"] = self._last_status_event.timestamp
        return status_event

    @property
    def status(self) -> Status:
        return self._last_status_event.status

    @status.setter
    def status(self, status: Status):
        if self.status <= Status.COMPLETE:
            now = time.time()
            self._status_history.append(StatusChangeEvent(status=status, timestamp=now))
            with self.status_file_path.open("a") as f:
                self.logger.debug(f"updating status: {status=}")
                f.write(f"{status.name},{now}\n")

    @property
    def running(self):
        return self.started and not self.finished

    @property
    def log_file_path(self) -> Path:
        return self._log_dir / Path(f"{self.query_id}.log")

    @property
    def status_file_path(self) -> Path:
        return self._status_dir / Path(f"{self.query_id}")

    @property
    def steps(self) -> Iterable[Step]:
        for step_class in self.step_classes:
            if not self.stopped:
                yield step_class.build_from_query(self)

    def start(self):
        self.start_time = time.time()
        try:
            for step in self.steps:
                if self.finished:
                    break
                self.logger.info(f"Starting: {step}")
                self.status = step.status
                self.current_step = step
                step.start()
                if not step.success:
                    self.crash()
        # pylint: disable=broad-exception-caught
        except Exception as e:
            # intentially crash on any python exception
            # as well as command failure
            self.logger.error(e)
            self.crash()
        if not self.finished:
            self.finish()

    def finish(self):
        self.status = Status.COMPLETE
        self.logger.info(f"Finishing: {self=}")
        if self.current_step:
            self.current_step.finish()
        self._cleanup()

    def kill(self):
        self.status = Status.KILLED
        self.logger.info(f"Killing: {self=}")
        if self.current_step:
            self.current_step.terminate()
        self._cleanup()

    def crash(self):
        self.status = Status.CRASHED
        self.logger.info(f"CRASHING! {self=}")
        if self.current_step:
            self.current_step.kill()
        self._cleanup()

    def _cleanup(self):
        self.current_step = None
        self.end_time = time.time()
        try:
            logger.remove(self._logger_id)
        except ValueError:
            pass
        if queries.get(self.query_id) is not None:
            del queries[self.query_id]

    @property
    def run_time(self):
        if not self.start_time:
            return 0
        if not self.end_time:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def cpu_usage_percent(self) -> float:
        if self.current_step:
            return self.current_step.cpu_usage_percent
        return 0

    @property
    def memory_rss_usage(self) -> int:
        if self.current_step:
            return self.current_step.memory_rss_usage
        return 0


QueryTypeT = TypeVar("QueryTypeT", bound=Query)
