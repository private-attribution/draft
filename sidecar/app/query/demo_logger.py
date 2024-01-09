from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import loguru

from .base import Query
from .command import LoggerOutputCommand
from .step import CommandStep, Status, Step


@dataclass(kw_only=True)
class DemoLoggerStep(CommandStep):
    num_lines: int
    total_runtime: int
    logger: loguru.Logger = field(repr=False)
    status: ClassVar[Status] = Status.IN_PROGRESS

    @classmethod
    def build_from_query(cls, query: "DemoLoggerQuery"):
        return cls(
            num_lines=query.num_lines,
            total_runtime=query.total_runtime,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f".venv/bin/python sidecar/logger "
            f"--num-lines {self.num_lines} "
            f"--total-runtime {self.total_runtime}",
            logger=self.logger,
        )


@dataclass(kw_only=True)
class DemoLoggerQuery(Query):
    num_lines: int
    total_runtime: int
    step_classes: ClassVar[list[type[Step]]] = [
        DemoLoggerStep,
    ]
