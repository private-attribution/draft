from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import shlex
import subprocess
import threading
import time
from typing import Dict, Optional
from loguru import logger
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

    def run(self, **kwargs):
        process = subprocess.Popen(
            shlex.split(self.cmd.format(**kwargs)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return process



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
            target=self.run_all,
            kwargs=kwargs,
            daemon=True,
        )
        thread.start()

    def run_step(self, step, **kwargs):
        self.status = step.start_status
        logger.info(self.status.name)
        logger.info("Starting: " + step.cmd.format(**kwargs))
        self.current_process = step.run(**kwargs)
        log_process_stdout(self.query_id, self.current_process)
        self.current_process.poll()
        logger.info(f"Return code: {self.current_process.returncode}")
        if self.current_process.returncode != 0:
            self.crash()
        self.status = step.end_status
        logger.info(self.status.name)

    def crash(self):
        self.status = Status.CRASHED
        logger.info("CRASHING!")
        self.finish()
        raise Exception("CRASHED")

    def finish(self):
        self.end_time = time.time()
        complete_semaphore = gen_process_complete_semaphore_path(self.query_id)
        complete_semaphore.touch()
        del queries[self.query_id]

    def run_all(self, **kwargs):
        self.start_time = time.time()
        for step in self.steps:
            self.run_step(step, **kwargs)
        self.finish()

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

ipa_compile_cmd = """
draft setup-helper --local_ipa_path {local_ipa_path} --branch {branch}
--commit_hash {commit_hash} --repeatable
"""

ipa_start_helper_cmd = """
draft start-helper --local_ipa_path {local_ipa_path}
--config_path {config_path} {identity}
"""

ipa_generate_test_data_cmd = """
draft generate-test-data --size {size} --test_data_path {test_data_path}
--local_ipa_path {local_ipa_path}
"""

ipa_start_ipa_cmd = """
draft start-ipa
  --local_ipa_path {local_ipa_path}
  --config_path {config_path}
  --max-breakdown-key {max_breakdown_key}
  --per-user-credit-cap {per_user_credit_cap}
  --test_data_file {test_data_file}
  --job_id {query_id}
"""

QuerySteps: Dict[str, list[Step]] = {
    "demo-logger": [
        Step(
            cmd=demo_logger_cmd,
            start_status=Status.IN_PROGRESS,
            end_status=Status.COMPLETE,
        ),
    ],
    "ipa-helper": [
        Step(
            cmd=ipa_compile_cmd,
            start_status=Status.COMPILING,
            end_status=Status.STARTING,
        ),
        Step(
            cmd=ipa_start_helper_cmd,
            start_status=Status.IN_PROGRESS,
            end_status=Status.COMPLETE,
        ),
    ],
    "ipa-coordinator": [
        Step(
            cmd=ipa_compile_cmd,
            start_status=Status.COMPILING,
            end_status=Status.WAITING_TO_START
        ),
        Step(
            cmd=ipa_generate_test_data_cmd,
            start_status=Status.WAITING_TO_START,
            end_status=Status.STARTING,
        ),
        Step(
            cmd=ipa_start_ipa_cmd,
            start_status=Status.IN_PROGRESS,
            end_status=Status.COMPLETE,
        ),
    ],
}
