from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import TYPE_CHECKING, ClassVar, Optional

import loguru

from .command import Command

if TYPE_CHECKING:
    from .base import Query


class Status(IntEnum):
    UNKNOWN = auto()
    STARTING = auto()
    COMPILING = auto()
    WAITING_TO_START = auto()
    IN_PROGRESS = auto()
    COMPLETE = auto()
    KILLED = auto()
    NOT_FOUND = auto()
    CRASHED = auto()


@dataclass(kw_only=True)
class Step:
    skip: bool = field(init=False, default=False)
    status: ClassVar[Status] = Status.UNKNOWN
    success: Optional[bool] = field(init=False, default=None)

    @classmethod
    def build_from_query(cls, query: Query):
        raise NotImplementedError

    def pre_run(self):
        pass

    def post_run(self):
        pass

    def run(self):
        raise NotImplementedError

    def start(self):
        self.pre_run()
        if not self.skip:
            self.run()
        self.post_run()
        if self.success is None:
            self.success = True

    def finish(self):
        self.terminate()
        self.success = True

    def terminate(self):
        raise NotImplementedError

    def kill(self):
        raise NotImplementedError

    @property
    def cpu_usage_percent(self) -> float:
        raise NotImplementedError

    @property
    def memory_rss_usage(self) -> int:
        raise NotImplementedError


@dataclass(kw_only=True)
class CommandStep(Step):
    env: Optional[dict] = field(default_factory=lambda: {**os.environ}, repr=False)
    command: Command = field(init=False, repr=True)

    def __post_init__(self):
        self.command = self.build_command()

    @classmethod
    def build_from_query(cls, query: Query):
        raise NotImplementedError

    def build_command(self) -> Command:
        raise NotImplementedError

    def run(self):
        self.command.start()
        if not self.success:
            self.success = self.command.returncode == 0

    def terminate(self):
        self.command.terminate()

    def kill(self):
        self.command.kill()

    @property
    def cpu_usage_percent(self) -> float:
        return self.command.cpu_usage_percent

    @property
    def memory_rss_usage(self) -> int:
        return self.command.memory_rss_usage


@dataclass(kw_only=True)
class LoggerOutputCommandStep(CommandStep):
    logger: loguru.Logger = field(repr=False)

    @classmethod
    def build_from_query(cls, query: Query):
        raise NotImplementedError

    def build_command(self) -> Command:
        raise NotImplementedError
