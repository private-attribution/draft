from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional, TypeVar

import loguru

from ..helpers import Role
from ..settings import get_settings
from .status import Status, StatusHistory
from .step import Step


class QueryExistsError(Exception):
    pass


def status_file_path(query_id: str) -> Path:
    settings = get_settings()
    return settings.status_dir_path / Path(query_id)


def log_file_path(query_id: str) -> Path:
    settings = get_settings()
    return settings.log_dir_path / Path(f"{query_id}.log")


@dataclass
class Query:
    """
    Query is the base class, used to implement a list of steps to be run by this server.
    The server has a role, obtained from get_settings().

    Steps implement a `build_from_query` method,
    which allows them to utilize data stored on the query.
    """

    # pylint: disable=too-many-instance-attributes
    query_id: str
    current_step: Optional[Step] = field(init=False, default=None, repr=True)
    logger: loguru.Logger = field(init=False, repr=False, compare=False)
    _logger_id: int = field(init=False, repr=False, compare=False)
    role: Role = field(init=False, repr=True)
    _status_history: StatusHistory = field(init=False, repr=True)
    step_classes: ClassVar[list[type[Step]]] = []

    def __post_init__(self):
        settings = get_settings()

        self.logger = settings.logger.bind(task=self.query_id)
        self.role = settings.role

        self._status_history = StatusHistory(
            file_path=self.status_file_path, logger=self.logger
        )

        self._logger_id = self.logger.add(
            self.log_file_path,
            serialize=True,
            filter=lambda record: record["extra"].get("task") == self.query_id,
            enqueue=True,
        )
        self.logger.debug(f"adding new Query {self}.")

    @property
    def status_file_path(self) -> Path:
        return status_file_path(self.query_id)

    @property
    def log_file_path(self) -> Path:
        return log_file_path(self.query_id)

    @property
    def started(self) -> bool:
        return self.status >= Status.STARTING

    @property
    def finished(self) -> bool:
        return self.status >= Status.COMPLETE

    @property
    def status(self) -> Status:
        return self._status_history.current_status

    @status.setter
    def status(self, status: Status):
        if self.status != status and self.status <= Status.COMPLETE:
            self._status_history.add(status)

    @property
    def status_event_json(self):
        return self._status_history.status_event_json

    @property
    def running(self):
        return self.started and not self.finished

    @property
    def steps(self) -> Iterable[Step]:
        for step_class in self.step_classes:
            yield step_class.build_from_query(self)

    def start(self):
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
        if self.running:
            self.status = Status.KILLED
            self.logger.info(f"Killing: {self=}")
            if self.current_step:
                self.current_step.terminate()
        self._cleanup()

    def crash(self):
        if self.running:
            self.status = Status.CRASHED
            self.logger.info(f"CRASHING! {self=}")
            if self.current_step:
                self.current_step.kill()
        self._cleanup()

    def _cleanup(self):
        self.current_step = None
        try:
            self.logger.remove(self._logger_id)
        except ValueError:
            pass

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


class MaxQueriesRunningError(Exception):
    pass


@dataclass
class QueryManager:
    """
    The QueryManager allows for a fixed number of queries to run at once,
    and stores those queries in a dictionary.

    Accessing running queries allows the finish and kill methods to be called
    from another caller (typically a route handler in the HTTP layer.
    """

    max_parallel_queries: int = field(init=True, repr=False, default=1)
    running_queries: dict[str, Query] = field(
        init=False, repr=True, default_factory=dict
    )

    def get_from_query_id(self, cls, query_id: str) -> Optional[Query]:
        if query_id in self.running_queries:
            return self.running_queries[query_id]
        if status_file_path(query_id).exists():
            return cls(query_id)
        return None

    def run_query(self, query: Query):
        if not self.capacity_available:
            raise MaxQueriesRunningError(
                f"Only {self.max_parallel_queries} allowed. Currently running {self}"
            )

        self.running_queries[query.query_id] = query
        try:
            query.start()
        finally:
            # always remove this
            del self.running_queries[query.query_id]

    @property
    def capacity_available(self):
        return len(self.running_queries) < self.max_parallel_queries
