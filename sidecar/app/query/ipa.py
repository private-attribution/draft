from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlunparse

import httpx
import loguru

from ..helpers import Role
from ..local_paths import Paths
from ..settings import settings
from .base import Query
from .command import FileOutputCommand, LoggerOutputCommand
from .step import CommandStep, LoggerOutputCommandStep, Status, Step


@dataclass(kw_only=True)
class IPAQuery(Query):
    paths: Paths

    def send_kill_signals(self):
        self.logger.info("sending kill signals")
        for helper in settings.helpers.values():
            if helper.role == self.role:
                continue
            finish_url = urlunparse(
                helper.sidecar_url._replace(
                    scheme="https", path=f"/stop/kill/{self.query_id}"
                ),
            )

            r = httpx.post(
                finish_url,
                verify=False,
            )
            self.logger.info(f"sent post request: {r.text}")

    def crash(self):
        super().crash()
        self.send_kill_signals()


@dataclass(kw_only=True)
class IPACloneStep(LoggerOutputCommandStep):
    repo_path: Path
    repo_url: ClassVar[str] = "https://github.com/private-attribution/ipa.git"
    status: ClassVar[Status] = Status.STARTING

    @classmethod
    def build_from_query(cls, query: IPAQuery):
        return cls(
            repo_path=query.paths.repo_path,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f"git clone {self.repo_url} {self.repo_path}",
            logger=self.logger,
        )

    def pre_run(self):
        if self.repo_path.exists():
            self.skip = True


@dataclass(kw_only=True)
class IPAFetchUpstreamStep(LoggerOutputCommandStep):
    repo_path: Path
    status: ClassVar[Status] = Status.STARTING

    @classmethod
    def build_from_query(cls, query: IPAQuery):
        return cls(
            repo_path=query.paths.repo_path,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f"git -C {self.repo_path} fetch --all",
            logger=self.logger,
        )


@dataclass(kw_only=True)
class IPACheckoutCommitStep(LoggerOutputCommandStep):
    repo_path: Path
    commit_hash: str
    status: ClassVar[Status] = Status.STARTING

    @classmethod
    def build_from_query(cls, query: IPAQuery):
        return cls(
            repo_path=query.paths.repo_path,
            commit_hash=query.paths.commit_hash,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f"git -C {self.repo_path} checkout {self.commit_hash}",
            logger=self.logger,
        )


@dataclass(kw_only=True)
class IPACorrdinatorCompileStep(LoggerOutputCommandStep):
    manifest_path: Path
    target_path: Path
    logger: loguru.Logger = field(repr=False)
    status: ClassVar[Status] = Status.COMPILING

    @classmethod
    def build_from_query(cls, query: IPAQuery):
        manifest_path = query.paths.repo_path / Path("Cargo.toml")
        target_path = query.paths.repo_path / Path(f"target-{query.paths.commit_hash}")
        return cls(
            manifest_path=manifest_path,
            target_path=target_path,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f"cargo build --bin report_collector "
            f"--manifest-path={self.manifest_path} "
            f'--features="clap cli test-fixture" '
            f"--target-dir={self.target_path} --release",
            logger=self.logger,
        )


@dataclass(kw_only=True)
class IPAHelperCompileStep(LoggerOutputCommandStep):
    manifest_path: Path
    target_path: Path
    logger: loguru.Logger = field(repr=False)
    status: ClassVar[Status] = Status.COMPILING

    @classmethod
    def build_from_query(cls, query: IPAQuery):
        manifest_path = query.paths.repo_path / Path("Cargo.toml")
        target_path = query.paths.repo_path / Path(f"target-{query.paths.commit_hash}")
        return cls(
            manifest_path=manifest_path,
            target_path=target_path,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f"cargo build --bin helper --manifest-path={self.manifest_path} "
            f'--features="web-app real-world-infra compact-gate stall-detection '
            f'multi-threading" --no-default-features --target-dir={self.target_path} '
            f"--release",
            logger=self.logger,
        )


@dataclass(kw_only=True)
class IPAHelperCollectStepsStep(CommandStep):
    repo_path: Path
    logger: loguru.Logger = field(repr=False)
    status: ClassVar[Status] = Status.COMPILING

    @classmethod
    def build_from_query(cls, query: IPAQuery):
        repo_path = query.paths.repo_path
        return cls(
            repo_path=repo_path,
            logger=query.logger,
        )

    def build_command(self) -> FileOutputCommand:
        output_file_path = self.repo_path / Path("ipa-core/src/protocol/step/steps.txt")
        return FileOutputCommand(
            cmd="python3 scripts/collect_steps.py -m",
            cwd=self.repo_path,
            output_file_path=output_file_path,
        )


@dataclass(kw_only=True)
class IPACoordinatorGenerateTestDataStep(CommandStep):
    output_file_path: Path
    report_collector_binary_path: Path
    size: int
    max_breakdown_key: int
    max_trigger_value: int
    status: ClassVar[Status] = Status.COMPILING

    def pre_run(self):
        self.output_file_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def build_from_query(cls, query: IPACoordinatorQuery):
        return cls(
            output_file_path=query.test_data_file,
            report_collector_binary_path=query.paths.report_collector_binary_path,
            size=query.size,
            max_breakdown_key=query.max_breakdown_key,
            max_trigger_value=query.max_trigger_value,
        )

    def build_command(self) -> FileOutputCommand:
        return FileOutputCommand(
            cmd=f"{self.report_collector_binary_path} gen-ipa-inputs -n {self.size} "
            f"--max-breakdown-key {self.max_breakdown_key} --report-filter all "
            f"--max-trigger-value {self.max_trigger_value} --seed 123",
            output_file_path=self.output_file_path,
        )


@dataclass(kw_only=True)
class IPACoordinatorWaitForHelpersStep(Step):
    query_id: str
    status: ClassVar[Status] = Status.WAITING_TO_START

    @classmethod
    def build_from_query(cls, query: IPAQuery):
        return cls(
            query_id=query.query_id,
        )

    def run(self):
        sidecar_urls = [
            helper.sidecar_url
            for helper in settings.helpers.values()
            if helper.role != Role.COORDINATOR
        ]
        for sidecar_url in sidecar_urls:
            url = urlunparse(
                sidecar_url._replace(
                    scheme="https", path=f"/start/ipa-helper/{self.query_id}/status"
                ),
            )
            while True:
                print(url)
                r = httpx.get(url, verify=False).json()
                print(r)
                status = r.get("status")
                match status:
                    case Status.IN_PROGRESS.name:
                        break
                    case Status.KILLED.name:
                        self.success = False
                        return
                    case Status.NOT_FOUND.name:
                        self.success = False
                        return
                    case Status.CRASHED.name:
                        self.success = False
                        return

                time.sleep(1)
        time.sleep(3)  # allow enough time for the command to start

    def terminate(self):
        return

    def kill(self):
        return

    @property
    def cpu_usage_percent(self) -> float:
        return 0

    @property
    def memory_rss_usage(self) -> int:
        return 0


@dataclass(kw_only=True)
class IPACoordinatorStartStep(LoggerOutputCommandStep):
    network_config: Path
    report_collector_binary_path: Path
    test_data_path: Path
    max_breakdown_key: int
    max_trigger_value: int
    per_user_credit_cap: int
    status: ClassVar[Status] = Status.IN_PROGRESS

    @classmethod
    def build_from_query(cls, query: IPACoordinatorQuery):
        return cls(
            network_config=query.paths.config_path / Path("network.toml"),
            report_collector_binary_path=query.paths.report_collector_binary_path,
            test_data_path=query.test_data_file,
            max_breakdown_key=query.max_breakdown_key,
            max_trigger_value=query.max_trigger_value,
            per_user_credit_cap=query.per_user_credit_cap,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f"{self.report_collector_binary_path} --network {self.network_config} "
            f"--input-file {self.test_data_path} oprf-ipa "
            f"--max-breakdown-key {self.max_breakdown_key} "
            f"--per-user-credit-cap {self.per_user_credit_cap} --plaintext-match-keys ",
            logger=self.logger,
        )


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
        IPACoordinatorWaitForHelpersStep,
        IPACoordinatorStartStep,
    ]

    def send_terminate_signals(self):
        self.logger.info("sending terminate signals")
        for helper in settings.helpers.values():
            if helper.role == self.role:
                continue
            finish_url = urlunparse(
                helper.sidecar_url._replace(
                    scheme="https", path=f"/stop/finish/{self.query_id}"
                ),
            )

            r = httpx.post(
                finish_url,
                verify=False,
            )
            self.logger.info(f"sent post request: {finish_url}: {r.text}")

    def finish(self):
        super().finish()
        self.send_terminate_signals()


@dataclass(kw_only=True)
class IPAStartHelperStep(LoggerOutputCommandStep):
    # pylint: disable=too-many-instance-attributes
    helper_binary_path: Path
    identity: int
    network_path: Path
    tls_cert_path: Path
    tls_key_path: Path
    mk_public_path: Path
    mk_private_path: Path
    port: int
    status: ClassVar[Status] = Status.IN_PROGRESS

    @classmethod
    def build_from_query(cls, query: IPAHelperQuery):
        identity = query.role.value
        network_path = query.paths.config_path / Path("network.toml")
        tls_cert_path = query.paths.config_path / Path(f"pub/h{identity}.pem")
        tls_key_path = query.paths.config_path / Path(f"h{identity}.key")
        mk_public_path = query.paths.config_path / Path(f"pub/h{identity}_mk.pub")
        mk_private_path = query.paths.config_path / Path(f"h{identity}_mk.key")
        return cls(
            helper_binary_path=query.paths.helper_binary_path,
            identity=identity,
            network_path=network_path,
            tls_cert_path=tls_cert_path,
            tls_key_path=tls_key_path,
            mk_public_path=mk_public_path,
            mk_private_path=mk_private_path,
            port=query.port,
            logger=query.logger,
        )

    def build_command(self) -> LoggerOutputCommand:
        return LoggerOutputCommand(
            cmd=f"{self.helper_binary_path} --network {self.network_path} "
            f"--identity {self.identity} --tls-cert {self.tls_cert_path} "
            f"--tls-key {self.tls_key_path} --port {self.port} "
            f"--mk-public-key {self.mk_public_path} "
            f"--mk-private-key {self.mk_private_path}",
            logger=self.logger,
        )


@dataclass(kw_only=True)
class IPAHelperQuery(IPAQuery):
    port: int

    step_classes: ClassVar[list[type[Step]]] = [
        IPACloneStep,
        IPAFetchUpstreamStep,
        IPACheckoutCommitStep,
        IPAHelperCompileStep,
        IPAHelperCollectStepsStep,
        IPAStartHelperStep,
    ]
