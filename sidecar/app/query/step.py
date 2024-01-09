from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import ClassVar, Optional

import loguru

from .command import Command


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


@dataclass
class Step:
    skip: bool = field(init=False, default=False)
    status: ClassVar[Status] = Status.UNKNOWN
    logger: loguru.Logger = field(init=False, repr=False)

    @classmethod
    def build_from_query(cls, query):
        raise NotImplementedError

    def pre_run(self):
        pass

    def post_run(self):
        pass

    def run(self):
        raise NotImplementedError

    def start(self):
        self.pre_run()
        if self.skip:
            self.logger.info(f"Skipped Step: {self}")
        else:
            self.run()
        self.post_run()

    def terminate(self):
        raise NotImplementedError

    def kill(self):
        raise NotImplementedError

    @property
    def returncode(self) -> int:
        raise NotImplementedError

    @property
    def cpu_usage_percent(self) -> float:
        raise NotImplementedError

    @property
    def memory_rss_usage(self) -> int:
        raise NotImplementedError


@dataclass
class CommandStep(Step):
    env: Optional[dict] = field(default_factory=lambda: {**os.environ}, repr=False)
    command: Command = field(init=False, repr=True)

    def __post_init__(self):
        self.command = self.build_command()

    def build_command(self) -> Command:
        raise NotImplementedError

    def run(self):
        self.command.start()

    def terminate(self):
        self.command.terminate()

    def kill(self):
        self.command.kill()

    @property
    def returncode(self) -> int:
        return self.command.returncode

    @property
    def cpu_usage_percent(self) -> float:
        return self.command.cpu_usage_percent

    @property
    def memory_rss_usage(self) -> int:
        return self.command.memory_rss_usage
