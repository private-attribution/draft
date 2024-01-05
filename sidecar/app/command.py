# pylint: disable=R0801,R0903
from __future__ import annotations

import os
import select
import shlex
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Command:
    cmd: str
    env: Optional[dict] = field(default_factory=lambda: {**os.environ}, repr=False)

    def get_process(self):
        return subprocess.Popen(
            shlex.split(self.cmd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def get_no_output_capture_process(self):
        return subprocess.Popen(
            shlex.split(self.cmd),
            env=self.env,
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

    def run_blocking_no_output_capture(self):
        with self.get_no_output_capture_process() as process:
            process.wait()


class PopenContextManager:
    def __init__(self, commands: list[Command]):
        self.commands = commands
        self.processes = []

    def __enter__(self):
        for command in self.commands:
            process = subprocess.Popen(
                shlex.split(command.cmd),
                env=command.env,
            )
            self.processes.append(process)

        return self.processes

    def __exit__(self, exc_type, exc_value, exc_tb):
        for process in self.processes:
            process.kill()


def start_commands_parallel(commands: list[Command]):
    with PopenContextManager(commands) as processes:
        for process in processes:
            process.wait()
