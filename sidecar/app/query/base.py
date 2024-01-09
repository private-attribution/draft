# pylint: disable=R0801
from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional

import loguru

from ..helpers import Role
from ..logger import logger
from ..settings import settings
from .step import Status, Step

# Dictionary to store queries
queries: dict[str, "Query"] = {}


@dataclass
class Query:
    # pylint: disable=too-many-instance-attributes
    query_id: str
    current_step: Optional[Step] = field(init=False, default=None, repr=True)
    _status: Status = field(init=False, default=Status.UNKNOWN)
    start_time: Optional[float] = field(init=False, default=None)
    end_time: Optional[float] = field(init=False, default=None)
    stopped: bool = field(init=False, default=False)
    logger: loguru.Logger = field(init=False, repr=False)
    _logger_id: int = field(init=False, repr=False)
    step_classes: ClassVar[list[type[Step]]] = []

    def __post_init__(self):
        self.logger = logger.bind(task=self.query_id)
        self.log_file_path.touch()
        self._logger_id = logger.add(
            self.log_file_path,
            format="{extra[role]}: {message}",
            filter=lambda record: record["extra"].get("task") == self.query_id,
            enqueue=True,
        )
        self.logger.debug(f"adding new Query {self}.")
        if queries.get(self.query_id) is not None:
            raise Exception(f"{self.query_id} already exists")
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
        query = cls(query_id)
        if query.status_file_path.exists():
            with query.status_file_path.open() as f:
                status_str = f.readline()
                query.status = Status[status_str]
                return query
        return None

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, status: Status):
        self._status = status
        with self.status_file_path.open("w+") as f:
            self.logger.debug(f"setting status: {status=}")
            f.write(str(status.name))

    @property
    def running(self):
        return self.started and not self.finished

    @property
    def log_file_path(self) -> Path:
        return settings.root_path / Path("logs") / Path(f"{self.query_id}.log")

    @property
    def status_file_path(self) -> Path:
        return settings.root_path / Path("status_semaphore") / Path(f"{self.query_id}")

    @property
    def steps(self) -> Iterable[Step]:
        for step_class in self.step_classes:
            if not self.stopped:
                yield step_class.build_from_query(self)

    def start(self):
        self.start_time = time.time()
        for step in self.steps:
            self.logger.info(f"Starting: {step}")
            self.status = step.status
            self.current_step = step
            step.start()
            self.logger.info(f"Return code: {step.returncode}")
            self.logger.info(f"{step=}")
            self.logger.info(f"{step.command=}")
            if step.returncode != 0:
                self.crash()
        if not self.finished:
            self.finish()

    def finish(self):
        self.status = Status.COMPLETE
        self.logger.info(f"Finishing: {self=}")
        if self.current_step:
            self.current_step.terminate()
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
