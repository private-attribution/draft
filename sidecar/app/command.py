import os
import shlex
import signal
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Command:
    cmd: str
    env: Optional[dict] = field(default_factory=lambda: {**os.environ})

    def run_blocking(self):
        with subprocess.Popen(
            shlex.split(self.cmd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ) as process:

            def sigterm_handler(_signum, _frame):
                process.terminate()

            signal.signal(signal.SIGTERM, sigterm_handler)
            signal.signal(signal.SIGINT, sigterm_handler)
            for line in process.stdout.readlines():
                print(line)
        return process
