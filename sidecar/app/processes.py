from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import shlex
import subprocess
import threading
import time
from typing import Dict, Optional
from .logging import log_process_stdout
from .settings import settings


complete_semaphore_path = settings.root_path / Path("complete_semaphore")
complete_semaphore_path.mkdir(exist_ok=True, parents=True)


def gen_process_complete_semaphore_path(process_id):
    return complete_semaphore_path / Path(f"{process_id}")


class Status(Enum):
    STARTING = auto()
    COMPILING = auto()
    WAITING_TO_START = auto()
    IN_PROGRESS = auto()
    COMPLETE = auto()
    NOT_FOUND = auto()
    CRASHED = auto()


@dataclass
class Step:
    cmd: str
    start_status: Status
    end_status: Status

    def run(self, query, **kwargs):
        process = subprocess.Popen(
            shlex.split(self.cmd.format(**kwargs)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        query.current_process = process
        log_process_stdout(query.query_id, process)
        return


@dataclass
class Query:
    query_id: str
    steps: list[Step]
    status: Status = Status.STARTING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    current_process: Optional[subprocess.Popen] = None

    def __post_init__(self):
        if queries.get(self.query_id) is not None:
            raise Exception(f"{self.query_id} already exists")
        queries[self.query_id] = self

    def run_in_thread(self, **kwargs):
        thread = threading.Thread(
            target=self.run,
            kwargs=kwargs,
            daemon=True,
        )
        thread.start()

    def run(self, **kwargs):
        self.start_time = time.time()
        for step in self.steps:
            self.status = step.start_status
            step.run(self, **kwargs)
            self.status = step.end_status
        self.end_time = time.time()
        complete_semaphore = gen_process_complete_semaphore_path(self.query_id)
        complete_semaphore.touch()
        del queries[self.query_id]

    @property
    def run_time(self):
        if not self.start_time:
            return 0
        if not self.end_time:
            return time.time() - self.start_time
        else:
            return self.end_time - self.start_time


# Dictionary to store process information
# processes: Dict[str, Tuple[subprocess.Popen, float]] = {}
queries: Dict[str, Query] = {}

demo_logger_cmd = """
.venv/bin/python sidecar/logger --num-lines {num_lines} --total-runtime {total_runtime}
"""


QuerySteps: Dict[str, list[Step]] = {
    "demo-logger": [
        Step(
            cmd=demo_logger_cmd,
            start_status=Status.IN_PROGRESS,
            end_status=Status.COMPLETE,
        ),
    ],
    # "ipa-helper": [Step(cmd)],
}
