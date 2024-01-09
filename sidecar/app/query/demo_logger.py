from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import Query
from .command import LoggerOutputCommand
from .step import LoggerOutputCommandStep, Status, Step


@dataclass(kw_only=True)
class DemoLoggerStep(LoggerOutputCommandStep):
    num_lines: int
    total_runtime: int
    status: ClassVar[Status] = Status.IN_PROGRESS

    @classmethod
    def build_from_query(cls, query: Query):
        if not isinstance(query, DemoLoggerQuery):
            raise ValueError(
                f"{cls.__name__} expects a DemoLoggerQuery, "
                f"but recieved {query.__class__}"
            )
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
