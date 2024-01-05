# pylint: disable=R0801
from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import ClassVar, Dict, Optional
from urllib.parse import urljoin, urlunparse

import httpx
import loguru
import websockets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from .command import (
    Command,
    FilePipeHandlerContextManager,
    LoggerPipeHandlerContextManager,
    PipeHandlerContextManager,
)
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
    UNKNOWN = auto()
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
    query: "Query" = field(repr=False)
    skip: bool = field(init=False, default=False)
    env: Optional[dict] = field(default_factory=lambda: {**os.environ}, repr=False)
    status: ClassVar[Status] = Status.UNKNOWN
    _pipe_handler: PipeHandlerContextManager = field(init=False, repr=False)

    @classmethod
    def build_from_query(cls, query):
        return cls(
            query=query,
        )

    def __post_init__(self):
        self._pipe_handler = LoggerPipeHandlerContextManager(logger=self.query.logger)

    @property
    def command(self) -> Command:
        raise NotImplementedError

    def pre_run(self):
        pass

    def post_run(self):
        pass

    @property
    def pipe_handler(self):
        return self._pipe_handler

    def run(self):
        self.pre_run()
        if self.skip:
            self.query.logger.info(f"Skipped Step: {self}")
        else:
            with self.pipe_handler as (stdout_handler, stderr_handler):
                with self.command.run(stdout_handler, stderr_handler) as process:
                    self.query.current_process = process
                    self.query.status = self.status
                    self.query.logger.info(f"{self.query.status.name=}")

        self.post_run()


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
        init=False, default=None, repr=True
    )
    _logger_id: int = field(init=False, repr=False)
    step_classes: ClassVar[list[type[Step]]] = []

    def __post_init__(self):
        self.logger = logger.bind(task=self.query_id)
        print(f"adding logger as {self.log_file_path}")
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
        self.steps = [
            step_class.build_from_query(self) for step_class in self.step_classes
        ]

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

    def run_step(self, step):
        if self.status >= Status.COMPLETE:
            self.logger.warning(f"Skipping {step=} run. Query has {self.status=}.")
            return
        self.logger.info(f"Starting: {step.command}")
        step.run()
        if self.current_process:
            self.logger.info(f"Return code: {self.current_process.returncode}")
            if self.current_process.returncode != 0 and self.status < Status.COMPLETE:
                self.crash()

    def finish(self):
        status = Status.COMPLETE
        self.logger.info(f"Finishing: {self=}")
        if self.running:
            self._terminate_current_process(status=status)
        else:
            self.status = status
        self._cleanup()

    def kill(self):
        status = Status.KILLED
        self.logger.info(f"Killing: {self=}")
        if self.running:
            self._kill_current_process(status=status)
        else:
            self.status = status
        self._cleanup()

    def crash(self):
        status = Status.CRASHED
        self.logger.info(f"CRASHING! {self=}")
        if self.running:
            self._kill_current_process(status=status)
        else:
            self.status = status
        self._cleanup()

    def _cleanup(self):
        self.current_process = None
        if not self.end_time:
            self.end_time = time.time()
        try:
            logger.remove(self._logger_id)
        except ValueError:
            pass
        if queries.get(self.query_id) is not None:
            del queries[self.query_id]

    def _terminate_current_process(self, status: Status):
        # typing work around so it knows current_process isn't None
        current_process = self.current_process
        if not self.running:
            self.logger.info("{self=} doesn't have a process to kill")
        elif current_process is not None:
            current_process.terminate()
            while current_process.poll() is None:
                continue
            self.logger.info(
                f"Process terminated. Return code: {current_process.returncode}"
            )
        self.status = status

    def _kill_current_process(self, status: Status):
        # typing work around so it knows current_process isn't None
        current_process = self.current_process
        if not self.running:
            self.logger.info("{self=} doesn't have a process to kill")
        elif current_process:
            current_process.kill()
            while current_process.poll() is None:
                continue
            self.logger.info(
                f"Process killed. Return code: {current_process.returncode}"
            )
        self.status = status

    def run_all(self):
        self.start_time = time.time()
        for step in self.steps:
            if self.status >= Status.COMPLETE:
                break
            self.run_step(step)
        if self.status < Status.COMPLETE:
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
    status: ClassVar[Status] = Status.IN_PROGRESS

    @property
    def command(self) -> Command:
        return Command(
            cmd=f".venv/bin/python sidecar/logger "
            f"--num-lines {self.query.num_lines} "
            f"--total-runtime {self.query.total_runtime}",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class DemoLoggerQuery(Query):
    num_lines: int
    total_runtime: int
    step_classes: ClassVar[list[type[Step]]] = [
        DemoLoggerStep,
    ]


@dataclass(kw_only=True)
class IPAStep(Step):
    query: "IPAQuery"

    @property
    def command(self) -> Command:
        raise NotImplementedError


@dataclass(kw_only=True)
class IPACloneStep(IPAStep):
    repo_url: ClassVar[str] = "https://github.com/private-attribution/ipa.git"
    status: ClassVar[Status] = Status.STARTING

    def pre_run(self):
        if self.query.paths.repo_path.exists():
            self.skip = True

    @property
    def command(self) -> Command:
        return Command(
            cmd=f"git clone {self.repo_url} {self.query.paths.repo_path}",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class IPAFetchUpstreamStep(IPAStep):
    status: ClassVar[Status] = Status.STARTING

    @property
    def command(self) -> Command:
        repo_path = self.query.paths.repo_path
        return Command(
            cmd=f"git -C {repo_path} fetch --all",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class IPACheckoutCommitStep(IPAStep):
    status: ClassVar[Status] = Status.STARTING

    @property
    def command(self) -> Command:
        repo_path = self.query.paths.repo_path
        commit_hash = self.query.paths.commit_hash
        return Command(
            cmd=f"git -C {repo_path} checkout {commit_hash}",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class IPAQuery(Query):
    paths: Paths

    def send_kill_signals(self):
        self.logger.info("sending kill signals")
        for helper in settings.helpers.values():
            if helper.role == self.role:
                continue
            finish_url = urljoin(
                helper.sidecar_url.geturl(), f"/stop/kill/{self.query_id}"
            )
            r = httpx.post(
                finish_url,
            )
            logger.info(f"sent post request: {r.text}")

    def crash(self):
        super().crash()
        self.send_kill_signals()


@dataclass(kw_only=True)
class IPACorrdinatorCompileStep(IPAStep):
    status: ClassVar[Status] = Status.COMPILING

    @property
    def command(self) -> Command:
        manifest_path = self.query.paths.repo_path / Path("Cargo.toml")
        target_path = self.query.paths.repo_path / Path(
            f"target-{self.query.paths.commit_hash}"
        )
        return Command(
            cmd=f"cargo build --bin report_collector --manifest-path={manifest_path} "
            f'--features="clap cli test-fixture" '
            f"--target-dir={target_path} --release",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class IPAHelperCompileStep(IPAStep):
    status: ClassVar[Status] = Status.COMPILING

    @property
    def command(self) -> Command:
        manifest_path = self.query.paths.repo_path / Path("Cargo.toml")
        target_path = self.query.paths.repo_path / Path(
            f"target-{self.query.paths.commit_hash}"
        )
        return Command(
            cmd=f"cargo build --bin helper --manifest-path={manifest_path} "
            f'--features="web-app real-world-infra compact-gate stall-detection" '
            f"--no-default-features --target-dir={target_path} --release",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class IPACoordinatorStep(IPAStep):
    query: "IPACoordinatorQuery"

    @property
    def command(self) -> Command:
        raise NotImplementedError


@dataclass(kw_only=True)
class IPACoordinatorGenerateTestDataStep(IPACoordinatorStep):
    status: ClassVar[Status] = Status.COMPILING

    @property
    def command(self) -> Command:
        report_collector_binary_path = self.query.paths.report_collector_binary_path
        size = self.query.size
        test_data_path = self.query.test_data_file
        max_breakdown_key = self.query.max_breakdown_key
        max_trigger_value = self.query.max_trigger_value

        self._pipe_handler = FilePipeHandlerContextManager(stdout_path=test_data_path)

        return Command(
            cmd=f"{report_collector_binary_path} gen-ipa-inputs -n {size} "
            f"--max-breakdown-key {max_breakdown_key} --report-filter all "
            f"--max-trigger-value {max_trigger_value} --seed 123",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class IPACoordinatorStartStep(IPACoordinatorStep):
    status: ClassVar[Status] = Status.IN_PROGRESS

    @property
    def command(self) -> Command:
        network_config = self.query.paths.config_path / Path("network.toml")
        report_collector_binary_path = self.query.paths.report_collector_binary_path
        test_data_path = self.query.test_data_file
        max_breakdown_key = self.query.max_breakdown_key
        per_user_credit_cap = self.query.per_user_credit_cap

        return Command(
            cmd=f"{report_collector_binary_path} --network {network_config} "
            f"--input-file {test_data_path} oprf-ipa "
            f"--max-breakdown-key {max_breakdown_key} "
            f"--per-user-credit-cap {per_user_credit_cap} --plaintext-match-keys ",
            pipe_handler=self.pipe_handler,
        )

    async def wait_for_status(self, helper_url, query_id):
        url = urlunparse(
            helper_url._replace(scheme="ws", path=f"/ws/status/{query_id}")
        )
        async with websockets.connect(url) as websocket:
            while True:
                status_json = await websocket.recv()
                status_data = json.loads(status_json)
                status = status_data.get("status")
                match status:
                    case "IN_PROGRESS":
                        return
                    case "NOT_FOUND":
                        raise Exception(f"{query_id=} doesn't exists.")

                self.query.logger.info(
                    f"Current status for {url=}: {status_data.get('status')}"
                )

                # Add a delay before checking again
                await asyncio.sleep(1)

    async def wait_for_helpers(self, helper_urls, query_id):
        tasks = [
            asyncio.create_task(self.wait_for_status(url, query_id))
            for url in helper_urls
        ]
        await asyncio.gather(*tasks)

    def pre_run(self):
        self.query.status = Status.WAITING_TO_START
        helper_urls = [
            helper.sidecar_url
            for helper in settings.helpers.values()
            if helper.role != Role.COORDINATOR
        ]
        self.query.logger.info(helper_urls)
        asyncio.run(self.wait_for_helpers(helper_urls, self.query.query_id))
        time.sleep(3)  # allow enough time for the command to start
        self.query.status = self.status


@dataclass(kw_only=True)
class IPACoordinatorQuery(IPAQuery):
    test_data_file: Path
    size: int
    max_breakdown_key: int
    max_trigger_value: int
    per_user_credit_cap: int
    step_classes: ClassVar[list[type[Step]]] = [
        IPACloneStep,
        IPAFetchUpstreamStep,
        IPACheckoutCommitStep,
        IPACorrdinatorCompileStep,
        IPACoordinatorGenerateTestDataStep,
        IPACoordinatorStartStep,
    ]

    def sign_query_id(self):
        return base64.b64encode(
            settings.private_key.sign(
                self.query_id.encode("utf8"), ec.ECDSA(hashes.SHA256())
            )
        ).decode("utf8")

    def send_terminate_signals(self):
        signature = self.sign_query_id()
        self.logger.info("sending terminate signals")
        for helper in settings.helpers.values():
            if helper.role == self.role:
                continue
            finish_url = urljoin(
                helper.sidecar_url.geturl(), f"/stop/finish/{self.query_id}"
            )
            r = httpx.post(
                finish_url,
                json={"identity": str(self.role.value), "signature": signature},
            )
            logger.info(f"sent post request: {finish_url}: {r.text}")

    def finish(self):
        super().finish()
        self.send_terminate_signals()


@dataclass(kw_only=True)
class IPAHelperStep(IPAStep):
    query: "IPAHelperQuery"

    @property
    def command(self) -> Command:
        raise NotImplementedError


@dataclass(kw_only=True)
class IPAStartHelperStep(IPAHelperStep):
    status: ClassVar[Status] = Status.IN_PROGRESS

    @property
    def command(self) -> Command:
        helper_binary_path = self.query.paths.helper_binary_path
        identity = self.query.role.value
        network_path = self.query.paths.config_path / Path("network.toml")
        tls_cert_path = self.query.paths.config_path / Path(f"pub/h{identity}.pem")
        tls_key_path = self.query.paths.config_path / Path(f"h{identity}.key")
        mk_public_path = self.query.paths.config_path / Path(f"pub/h{identity}_mk.pub")
        mk_private_path = self.query.paths.config_path / Path(f"h{identity}_mk.key")
        port = self.query.port

        return Command(
            cmd=f"{helper_binary_path} --network {network_path} "
            f"--identity {identity} --tls-cert {tls_cert_path} "
            f"--tls-key {tls_key_path} --port {port} "
            f"--mk-public-key {mk_public_path} "
            f"--mk-private-key {mk_private_path}",
            pipe_handler=self.pipe_handler,
        )


@dataclass(kw_only=True)
class IPAHelperQuery(IPAQuery):
    port: int

    step_classes: ClassVar[list[type[Step]]] = [
        IPACloneStep,
        IPAFetchUpstreamStep,
        IPACheckoutCommitStep,
        IPAHelperCompileStep,
        IPAStartHelperStep,
    ]
