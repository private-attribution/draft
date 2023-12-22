import os
import shlex
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Command:
    cmd: str
    env: Optional[dict] = field(default_factory=lambda: {**os.environ})

    def run_blocking(self):
        result = subprocess.run(
            shlex.split(self.cmd),
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stderr)
        print(result.stdout)
        return result
