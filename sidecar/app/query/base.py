from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional, TypeVar

import loguru

from ..helpers import Role
from ..logger import get_logger
from ..settings import get_settings
from .status import Status, StatusHistory
from .step import Step

# Dictionary to store queries
queries: dict[str, "Query"] = {}


class QueryExistsError(Exception):
    pass


@dataclass
class Query:
    # pylint: disable=too-many-instance-attributes
    query_id: str
    current_step: Optional[Step] = field(init=False, default=None, repr=True)
    logger: loguru.Logger = field(init=False, repr=False)
    _logger_id: int = field(init=False, repr=False)
    log_file_path: Path = field(init=False, repr=False)
    role: Role = field(init=False, repr=True)
    _status_history: StatusHistory = field(init=False, repr=True)
    step_classes: ClassVar[list[type[Step]]] = []

    def __post_init__(self):
        settings = get_settings()
        logger = get_logger()

        self.logger = logger.bind(task=self.query_id)
        self.role = settings.role

        status_dir = settings.root_path / Path("status")
        status_dir.mkdir(exist_ok=True)
        status_file_path = status_dir / Path(f"{self.query_id}")
        self._status_history = StatusHistory(file_path=status_file_path, logger=logger)

        log_dir = settings.root_path / Path("logs")
        self.log_file_path = log_dir / Path(f"{self.query_id}.log")
        log_dir.mkdir(exist_ok=True)
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
    def started(self) -> bool:
        return self.status >= Status.STARTING

    @property
    def finished(self) -> bool:
        return self.status >= Status.COMPLETE

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
        if query.status == Status.UNKNOWN:
            # pylint: disable=protected-access
            query._cleanup()
            return None
        return query

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
        if queries.get(self.query_id) is not None:
            del queries[self.query_id]

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
