# pylint: disable=R0801,R0903
from __future__ import annotations

import asyncio
import os
import select
import shlex
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import loguru


class PipeHandlerContextManager:
    def __enter__(self) -> tuple[Callable[[str], None], Callable[[str], None]]:
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


def print_wrapper(line: str) -> None:
    sys.stdout.write(line)


class PrintPipeHandlerContextManager(PipeHandlerContextManager):
    def __enter__(self) -> tuple[Callable[[str], None], Callable[[str], None]]:
        return print_wrapper, print_wrapper


class LoggerPipeHandlerContextManager(PipeHandlerContextManager):
    def __init__(self, logger: loguru.Logger):
        self.logger = logger

    def __enter__(self) -> tuple[Callable[[str], None], Callable[[str], None]]:
        def info_wrapper(line: str) -> None:
            self.logger.info(line.rstrip("\n"))

        def warning_wrapper(line: str) -> None:
            self.logger.warning(line.rstrip("\n"))

        return info_wrapper, warning_wrapper


class FilePipeHandlerContextManager(PipeHandlerContextManager):
    def __init__(self, stdout_path: Path):
        self.stdout_path = stdout_path
        self.stdout_f = None

    def __enter__(self) -> tuple[Callable[[str], None], Callable[[str], None]]:
        self.stdout_f = self.stdout_path.open("w", encoding="utf8")

        def stdout_wrapper(line: str) -> None:
            self.stdout_f.write(line)

        return stdout_wrapper, print_wrapper

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stdout_f.close()


@dataclass
class Command:
    cmd: str
    env: Optional[dict] = field(default_factory=lambda: {**os.environ}, repr=False)
    pipe_handler: Optional[PipeHandlerContextManager] = field(
        default_factory=PrintPipeHandlerContextManager,
        repr=False,
    )

    def get_process(self):
        return subprocess.Popen(
            shlex.split(self.cmd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    async def get_async_process(self):
        return await asyncio.create_subprocess_exec(
            *shlex.split(self.cmd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @contextmanager
    def run(self, stdout_handler, stderr_handler):
        with self.get_process() as process:
            yield process
            stdout_fileno = process.stdout.fileno()
            stderr_fileno = process.stderr.fileno()
            while process.poll() is None:
                readable, _, _ = select.select([stdout_fileno, stderr_fileno], [], [])
                for fd in readable:
                    if fd == stdout_fileno:
                        stdout_line = process.stdout.readline()
                        if stdout_line:
                            stdout_handler(stdout_line)
                    elif fd == stderr_fileno:
                        stderr_line = process.stderr.readline()
                        if stderr_line:
                            stderr_handler(stderr_line)
            for line in process.stdout:
                stdout_handler(line)

            for line in process.stderr:
                stderr_handler(line)

    def run_blocking(self):
        with self.pipe_handler as (stdout_handler, stderr_handler):
            print(f"Starting subprocess: {self}\n")
            with self.run(stdout_handler, stderr_handler):
                pass


async def read_stream(
    stream: asyncio.StreamReader,
    handler: Callable[[str], None],
) -> None:
    while True:
        line = await stream.readline()
        if not line:
            break
        handler(line.decode("utf-8"))


class ParallelCommandsContextManager:
    def __init__(self, commands: list[Command]):
        self.commands = commands
        self.processes = []

    async def run_command(self, command, stdout_handler, stderr_handler):
        print(f"Starting subprocess: {command}")
        process = await command.get_async_process()
        stdout_task = asyncio.create_task(read_stream(process.stdout, stdout_handler))
        stderr_task = asyncio.create_task(read_stream(process.stderr, stderr_handler))
        await asyncio.gather(stdout_task, stderr_task)
        return await process.wait()

    async def __aenter__(self):
        for command in self.commands:
            with command.pipe_handler as (stdout_handler, stderr_handler):
                process = self.run_command(command, stdout_handler, stderr_handler)
                self.processes.append(process)

        return self.processes

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        pass


async def start_commands_parallel(commands: list[Command]):
    async with ParallelCommandsContextManager(commands=commands) as processes:
        await asyncio.gather(*processes)
