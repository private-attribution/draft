from __future__ import annotations

import base64
import shlex
import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urljoin

import httpx
import loguru
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from .helpers import Role
from .local_paths import Paths
from .logger import logger
from .settings import settings

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
    KILLED = auto()
    NOT_FOUND = auto()
    CRASHED = auto()


@dataclass
class Step:
    cmd: str
    status: Status
    query: "Query" = field(repr=False)

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
    # pylint: disable=too-many-instance-attributes
    query_id: str
    steps: list[Step] = field(default_factory=list, repr=False)
    logger: loguru.Logger = field(init=False, repr=False)
    role: Role = field(init=False, default=settings.role, repr=False)
    _status: Status = field(init=False, default=Status.STARTING)
    start_time: Optional[float] = field(init=False, default=None)
    end_time: Optional[float] = field(init=False, default=None)
    current_process: Optional[subprocess.Popen] = field(
        init=False, default=None, repr=False
    )
    _logger_id: int = field(init=False, repr=False)

    def __post_init__(self):
        self.logger = logger.bind(task=self.query_id)
        self._logger_id = logger.add(
            self.log_file_path,
            format="{extra[role]}: {message}",
            filter=lambda record: record["extra"].get("task") == self.query_id,
            enqueue=True,
            encoding="utf8",
        )
        self.logger.debug(f"adding new Query {self}.")
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
        if self.current_process.returncode != 0 and self.status != Status.COMPLETE:
            self.crash()

    def finish(self):
        self.status = Status.COMPLETE
        if self.running:
            self._terminate_current_process()
        self.logger.info("Terminating process.")
        self.logger.info(f"Return code: {self.current_process.returncode}")
        self._cleanup()

    def kill(self):
        self.status = Status.KILLED
        self.logger.info(f"Killed. {self=}")
        if self.running:
            self._kill_current_process()
        self.logger.info("Killing process.")
        self.logger.info(f"Return code: {self.current_process.returncode}")
        self._cleanup()

    def crash(self):
        self.status = Status.CRASHED
        self.logger.info(f"CRASHING! {self=}")
        if self.running:
            self._kill_current_process()
        self.logger.info("Killing process.")
        self.logger.info(f"Return code: {self.current_process.returncode}")
        self._cleanup()

    def _cleanup(self):
        self.end_time = time.time()
        logger.remove(self._logger_id)
        del queries[self.query_id]

    def _terminate_current_process(self):
        if self.current_process is None:
            raise Exception("{self=} doesn't have a process to kill")
        self.current_process.terminate()

    def _kill_current_process(self):
        if self.current_process is None:
            raise Exception("{self=} doesn't have a process to kill")
        self.current_process.kill()

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
        self.steps = [
            DemoLoggerStep(
                query=self,
                cmd=demo_logger_cmd,
                status=Status.IN_PROGRESS,
            )
        ]
        super().__post_init__()


@dataclass(kw_only=True)
class IPAStep(Step):
    query: "IPAQuery"


@dataclass(kw_only=True)
class IPAQuery(Query):
    paths: Paths

    @property
    def commit_hash_str(self):
        if self.paths.commit_hash:
            return " --commit_hash " + self.paths.commit_hash
        return ""

    @property
    def branch_str(self):
        if self.paths.branch:
            return " --branch " + self.paths.branch
        return ""


@dataclass(kw_only=True)
class IPACoordinatorQuery(IPAQuery):
    test_data_file: Path
    size: int
    max_breakdown_key: int
    max_trigger_value: int
    per_user_credit_cap: int

    def __post_init__(self):
        ipa_compile_cmd = (
            f"draft setup-coordinator --local_ipa_path {self.paths.repo_path}"
            f"{self.branch_str} {self.commit_hash_str} --repeatable"
        )
        ipa_generate_test_data_cmd = (
            f"draft generate-test-data --size {self.size}"
            f"{self.branch_str} {self.commit_hash_str}"
            f" --max-breakdown-key {self.max_breakdown_key}"
            f" --max-trigger-value {self.max_trigger_value}"
            f" --test_data_path {self.paths.test_data_path}"
            f" --local_ipa_path {self.paths.repo_path}"
        )
        ipa_start_ipa_cmd = (
            f"draft start-ipa"
            f"{self.branch_str} {self.commit_hash_str}"
            f" --local_ipa_path {self.paths.repo_path}"
            f" --config_path {self.paths.config_path}"
            f" --max-breakdown-key {self.max_breakdown_key}"
            f" --per-user-credit-cap {self.per_user_credit_cap}"
            f" --test_data_file {self.test_data_file}"
            f" --query_id {self.query_id}"
        )

        self.steps = [
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

    def sign_query_id(self):
        return base64.b64encode(
            settings.private_key.sign(
                self.query_id.encode("utf8"), ec.ECDSA(hashes.SHA256())
            )
        ).decode("utf8")

    def send_finish_signals(self):
        signature = self.sign_query_id()
        self.logger.info("sending finish signals")
        for helper in settings.helpers.values():
            if helper.role == self.role:
                pass
            finish_url = urljoin(
                helper.sidecar_url.geturl(), f"/stop/finish/{self.query_id}"
            )
            r = httpx.post(
                finish_url,
                json={"identity": str(self.role.value), "signature": signature},
            )
            logger.info(f"sent post request: {r.text}")

    def finish(self):
        super().finish()
        self.send_finish_signals()


@dataclass(kw_only=True)
class IPAHelperQuery(IPAQuery):
    def __post_init__(self):
        ipa_compile_cmd = (
            f"draft setup-helper --local_ipa_path {self.paths.repo_path}"
            f"{self.branch_str} {self.commit_hash_str}"
            f" --repeatable"
        )

        ipa_start_helper_cmd = (
            f"draft start-helper --local_ipa_path {self.paths.repo_path}"
            f"{self.branch_str} {self.commit_hash_str}"
            f" --config_path {self.paths.config_path} {self.role.value}"
        )

        self.steps = [
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
