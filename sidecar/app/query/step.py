from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import TYPE_CHECKING, ClassVar, Optional

import loguru

from .command import Command

if TYPE_CHECKING:
    from .base import QueryTypeT


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
class Step(ABC):
    skip: bool = field(init=False, default=False)
    status: ClassVar[Status] = Status.UNKNOWN
    success: Optional[bool] = field(init=False, default=None)

    @classmethod
    @abstractmethod
    def build_from_query(cls, query: QueryTypeT):
        ...

    def pre_run(self):
        pass

    def post_run(self):
        pass

    @abstractmethod
    def run(self):
        ...

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

    @abstractmethod
    def terminate(self):
        ...

    @abstractmethod
    def kill(self):
        ...

    @property
    @abstractmethod
    def cpu_usage_percent(self) -> float:
        ...

    @property
    @abstractmethod
    def memory_rss_usage(self) -> int:
        ...


@dataclass(kw_only=True)
class CommandStep(Step, ABC):
    env: Optional[dict] = field(default_factory=lambda: {**os.environ}, repr=False)
    command: Command = field(init=False, repr=True)

    def __post_init__(self):
        self.command = self.build_command()

    @abstractmethod
    def build_command(self) -> Command:
        ...

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
class LoggerOutputCommandStep(CommandStep, ABC):
    logger: loguru.Logger = field(repr=False)
