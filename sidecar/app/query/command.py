from __future__ import annotations

import os
import select
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TextIO

import loguru
import psutil


@dataclass
class Command:
    cmd: str
    env: Optional[dict] = field(default_factory=lambda: {**os.environ}, repr=False)
    process: Optional[subprocess.Popen] = field(init=False, default=None, repr=True)

    @property
    def returncode(self):
        process = self.process
        if process is None:
            return None
        return process.returncode

    @property
    def started(self):
        return self.process is not None

    @property
    def finished(self):
        return self.returncode is not None

    @property
    def running(self):
        return self.started and not self.finished

    @property
    def process_psutil(self) -> Optional[psutil.Process]:
        process = self.process
        if process is None:
            return None
        return psutil.Process(process.pid)

    @property
    def cpu_usage_percent(self) -> float:
        process_psutil = self.process_psutil
        if process_psutil is None:
            return 0
        return process_psutil.cpu_percent()

    @property
    def memory_rss_usage(self) -> int:
        process_psutil = self.process_psutil
        if process_psutil is None:
            return 0
        return process_psutil.memory_info().rss

    def build_process(self):
        return subprocess.Popen(
            shlex.split(self.cmd),
            env=self.env,
        )

    def start(self):
        self.process = self.build_process()
        self.process.wait()

    def terminate(self):
        process = self.process
        if process is not None:
            process.terminate()
            process.wait()

    def kill(self):
        process = self.process
        if process is not None:
            process.kill()
            process.wait()


@dataclass(kw_only=True)
class FileOutputCommand(Command):
    output_file_path: Path
    output_file: Optional[TextIO] = field(repr=False, init=False)

    def __post_init__(self):
        # need to manually close in start method
        # pylint: disable=consider-using-with
        self.output_file = self.output_file_path.open("w", encoding="utf8")

    @property
    def new_process(self):
        return subprocess.Popen(
            shlex.split(self.cmd),
            stdout=self.output_file,
            env=self.env,
        )

    def start(self):
        super().start()
        self.output_file.close()


@dataclass(kw_only=True)
class LoggerOutputCommand(Command):
    logger: loguru.Logger = field(repr=False)

    @property
    def new_process(self):
        return subprocess.Popen(
            shlex.split(self.cmd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def start(self):
        with self.new_process as process:
            self.process = process
            stdout_fileno = process.stdout.fileno()
            stderr_fileno = process.stderr.fileno()
            while process.poll() is None:
                readable, _, _ = select.select([stdout_fileno, stderr_fileno], [], [])
                for fd in readable:
                    if fd == stdout_fileno:
                        stdout_line = process.stdout.readline()
                        if stdout_line:
                            self.logger.info(stdout_line.rstrip("\n"))
                    elif fd == stderr_fileno:
                        stderr_line = process.stderr.readline()
                        if stderr_line:
                            self.logger.info(stderr_line.rstrip("\n"))
            for line in process.stdout:
                self.logger.info(line.rstrip("\n"))

            for line in process.stderr:
                self.logger.info(line.rstrip("\n"))


class ParallelCommandContextManager:
    def __init__(self, commands: list[Command]):
        self.commands = commands
        self.processes = []

    def __enter__(self):
        for command in self.commands:
            self.processes.append(command.new_process)
        return self.processes

    def __exit__(self, exc_type, exc_value, exc_tb):
        for process in self.processes:
            process.kill()


def start_commands_parallel(commands: list[Command]):
    with ParallelCommandContextManager(commands) as processes:
        for process in processes:
            process.wait()
