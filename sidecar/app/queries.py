from __future__ import annotations

import shlex
import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import Dict, Optional

import loguru

from .logger import logger
from .settings import Role, settings

complete_semaphore_path = settings.root_path / Path("complete_semaphore")
complete_semaphore_path.mkdir(exist_ok=True, parents=True)
status_semaphore_path = settings.root_path / Path("status_semaphore")
status_semaphore_path.mkdir(exist_ok=True, parents=True)
log_path = settings.root_path / Path("logs")
log_path.mkdir(exist_ok=True, parents=True)

# Dictionary to store queries
queries: Dict[str, "Query"] = {}


def gen_process_complete_semaphore_path(query_id):
    return complete_semaphore_path / Path(f"{query_id}")


class Status(IntEnum):
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
    status: Status
    query: "Query"

    @contextmanager
    def run(self):
        process = subprocess.Popen(
            shlex.split(self.cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        yield process
        while process.poll() is None:
            line = process.stdout.readline()
            if not line:
                continue
            self.query.logger.info(line.rstrip("\n"))


@dataclass
class Query:
    query_id: str
    role: Role = settings.role
    logger: loguru.Logger = logger
    _steps: Optional[list[Step]] = None
    _status: Status = field(init=False, default=Status.STARTING)
    start_time: Optional[float] = field(init=False, default=None)
    end_time: Optional[float] = field(init=False, default=None)
    current_process: Optional[subprocess.Popen] = field(init=False, default=None)

    def __post_init__(self):
        self.logger = logger.bind(task=self.query_id)
        logger.add(
            self.log_file_path,
            format="{extra[role]}: {message}",
            filter=lambda record: record["extra"].get("task") == self.query_id,
            enqueue=True,
            encoding="utf8",
        )
        self.logger.debug(f"adding new Query{self=}. all queries: {queries}")
        if queries.get(self.query_id) is not None:
            raise Exception(f"{self.query_id} already exists")
        self.log_file_path.touch()
        queries[self.query_id] = self

    @classmethod
    def get_from_query_id(cls, query_id) -> Optional["Query"]:
        query = queries.get(query_id)
        if query:
            return query
        query = cls(query_id)
        if query.status_file_path.exists():
            with query.status_file_path.open() as f:
                status_str = f.readline()
                query.status = Status[status_str]
                return query
        return None

    @property
    def steps(self):
        if not self._steps:
            raise NotImplementedError(f"{self.__class__} does not implement steps.")
        return self._steps

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, status: Status):
        self._status = status
        with self.status_file_path.open("w+") as f:
            self.logger.debug(f"setting status: {status=}")
            f.write(str(status.name))

    @property
    def running(self):
        if self.done:
            return False
        return self.current_process is not None and self.current_process.poll() is None

    @property
    def done(self):
        return self.status >= Status.COMPLETE

    @property
    def log_file_path(self) -> Path:
        return log_path / Path(f"{self.query_id}.log")

    @property
    def status_file_path(self) -> Path:
        return status_semaphore_path / Path(f"{self.query_id}")

    def run_in_thread(self):
        thread = threading.Thread(
            target=self.run_all,
            daemon=True,
        )
        thread.start()

    def run_step(self, step):
        if self.status >= Status.COMPLETE:
            self.logger.warning(f"Skipping {step=} run. Query has {self.status=}.")
            return
        self.status = step.status
        self.logger.info(f"{self.status.name=}")
        self.logger.info("Starting: " + step.cmd)
        with step.run() as process:
            self.current_process = process
        self.logger.info(f"Return code: {self.current_process.returncode}")
        if self.current_process.returncode != 0:
            self.crash()

    def crash(self):
        self.status = Status.CRASHED
        self.logger.info("CRASHING!")
        self.finish()
        raise Exception("CRASHED")

    def finish(self):
        self.end_time = time.time()
        del queries[self.query_id]

    def run_all(self, **kwargs):
        self.start_time = time.time()
        for step in self.steps:
            self.run_step(step, **kwargs)
        self.status = Status.COMPLETE
        self.finish()

    @property
    def run_time(self):
        if not self.start_time:
            return 0
        if not self.end_time:
            return time.time() - self.start_time
        return self.end_time - self.start_time


@dataclass(kw_only=True)
class DemoLoggerStep(Step):
    query: "DemoLoggerQuery"


@dataclass(kw_only=True)
class DemoLoggerQuery(Query):
    num_lines: int
    total_runtime: int

    def __post_init__(self):
        demo_logger_cmd = f"""
        .venv/bin/python sidecar/logger --num-lines {self.num_lines}
        --total-runtime {self.total_runtime}
        """
        self._steps = [
            DemoLoggerStep(
                query=self,
                cmd=demo_logger_cmd,
                status=Status.IN_PROGRESS,
            )
        ]
        super().__post_init__()


@dataclass(kw_only=True)
class IPAStep(Step):
    query: "IPACoordinatorQuery | IPAHelperQuery"


@dataclass(kw_only=True)
class IPACoordinatorQuery(Query):
    local_ipa_path: Path
    test_data_path: Path
    test_data_file: Path
    config_path: Path
    size: int
    max_breakdown_key: int
    max_trigger_value: int
    per_user_credit_cap: int
    branch: Optional[str] = None
    commit_hash: Optional[str] = None

    def __post_init__(self):
        ipa_compile_cmd = (
            f"draft setup-coordinator --local_ipa_path {self.local_ipa_path}"
            f"{' --branch ' + self.branch if self.branch else ''}"
            f"{' --commit_hash ' + self.commit_hash if self.commit_hash else ''}"
            f" --repeatable"
        )
        ipa_generate_test_data_cmd = (
            f"draft generate-test-data --size {self.size}"
            f"{' --branch ' + self.branch if self.branch else ''}"
            f"{' --commit_hash ' + self.commit_hash if self.commit_hash else ''}"
            f" --max-breakdown-key {self.max_breakdown_key}"
            f" --max-trigger-value {self.max_trigger_value}"
            f" --test_data_path {self.test_data_path}"
            f" --local_ipa_path {self.local_ipa_path}"
        )
        ipa_start_ipa_cmd = (
            f"draft start-ipa"
            f"{' --branch ' + self.branch if self.branch else ''}"
            f"{' --commit_hash ' + self.commit_hash if self.commit_hash else ''}"
            f" --local_ipa_path {self.local_ipa_path}"
            f" --config_path {self.config_path}"
            f" --max-breakdown-key {self.max_breakdown_key}"
            f" --per-user-credit-cap {self.per_user_credit_cap}"
            f" --test_data_file {self.test_data_file}"
            f" --query_id {self.query_id}"
        )

        self._steps = [
            IPAStep(
                query=self,
                cmd=ipa_compile_cmd,
                status=Status.COMPILING,
            ),
            IPAStep(
                query=self,
                cmd=ipa_generate_test_data_cmd,
                status=Status.STARTING,
            ),
            IPAStep(
                query=self,
                cmd=ipa_start_ipa_cmd,
                status=Status.IN_PROGRESS,
            ),
        ]
        super().__post_init__()


@dataclass(kw_only=True)
class IPAHelperQuery(Query):
    local_ipa_path: Path
    config_path: Path
    branch: Optional[str] = None
    commit_hash: Optional[str] = None

    def __post_init__(self):
        ipa_compile_cmd = (
            f"draft setup-helper --local_ipa_path {self.local_ipa_path}"
            f"{' --branch ' + self.branch if self.branch else ''}"
            f"{' --commit_hash ' + self.commit_hash if self.commit_hash else ''}"
            f" --repeatable"
        )

        ipa_start_helper_cmd = (
            f"draft start-helper --local_ipa_path {self.local_ipa_path}"
            f"{' --branch ' + self.branch if self.branch else ''}"
            f"{' --commit_hash ' + self.commit_hash if self.commit_hash else ''}"
            f" --config_path {self.config_path} {self.role.value}"
        )

        self._steps = [
            IPAStep(
                query=self,
                cmd=ipa_compile_cmd,
                status=Status.COMPILING,
            ),
            IPAStep(
                query=self,
                cmd=ipa_start_helper_cmd,
                status=Status.IN_PROGRESS,
            ),
        ]
        super().__post_init__()
