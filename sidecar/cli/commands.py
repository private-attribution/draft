import asyncio
import itertools
import json
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlunparse

import click
import websockets

from ..app.helpers import Role, load_helpers_from_network_config


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


def process_result(success_msg, returncode, failure_message=None):
    if returncode == 0:
        click.echo(click.style(success_msg, fg="green"))
    else:
        click.echo(click.style("Failure!", blink=True, bold=True, bg="red", fg="white"))
        if failure_message is not None:
            click.echo(click.style(failure_message, bold=True))
        raise SystemExit(1)


class PopenContextManager:
    def __init__(self, commands: list[Command], popen_args=None):
        self.commands = commands
        self.processes = []
        if popen_args is not None:
            self.popen_args = popen_args
        else:
            self.popen_args = {}

    def __enter__(self):
        for command in self.commands:
            process = subprocess.Popen(
                shlex.split(command.cmd), env=command.env, **self.popen_args
            )
            self.processes.append(process)
        return self.processes

    def __exit__(self, exc_type, exc_value, exc_tb):
        for process in self.processes:
            process.kill()


def clone(local_ipa_path, exists_ok):
    # setup
    if local_ipa_path.exists():
        if exists_ok:
            process_result(f"{local_ipa_path=} exists. Skipping clone.", 0)
            return
        process_result("", 1, f"Run in isolated mode and {local_ipa_path=} exists.")

    command = Command(
        cmd=f"git clone https://github.com/private-attribution/ipa.git {local_ipa_path}"
    )
    result = command.run_blocking()
    process_result("Success: IPA cloned.", result.returncode, result.stderr)


def get_branch_commit_hash(local_ipa_path: Path, branch: str) -> str:
    command = Command(cmd=f"git -C {local_ipa_path} fetch --all")
    result = command.run_blocking()
    process_result("Success: upstream fetched.", result.returncode, result.stderr)
    command = Command(cmd=f"git -C {local_ipa_path} rev-parse origin/{branch}")
    result = command.run_blocking()
    process_result(
        f"Success: {branch} is at {result.stdout.strip()}.",
        result.returncode,
        result.stderr,
    )
    return result.stdout.strip()
def checkout_commit(local_ipa_path: Path, commit_hash: str):
    command = Command(cmd=f"git -C {local_ipa_path} fetch --all")
    result = command.run_blocking()
    process_result("Success: upstream fetched.", result.returncode, result.stderr)
    command = Command(cmd=f"git -C {local_ipa_path} checkout {commit_hash}")
    result = command.run_blocking()
    process_result(f"Success: Checked out {commit_hash}.", result.returncode)


def checkout_branch(local_ipa_path: Path, branch: str):
    commit_hash = get_branch_commit_hash(local_ipa_path, branch)
    process_result(f"Checking out {branch} @ {commit_hash}", 0)
    checkout_commit(local_ipa_path, commit_hash)


def compile_(
    local_ipa_path: Path,
    target_path: Path,
    binary_name: str,
    features: str,
    default_features: bool,
):
    manifest_path = local_ipa_path / Path("Cargo.toml")
    command = Command(
        cmd=f"""cargo build --bin {binary_name} --manifest-path={manifest_path}
        --features="{features}"
        {'--no-default-features' if not default_features else ''}
        --target-dir={target_path} --release"""
    )
    print(command.cmd)
    result = command.run_blocking()
    process_result("Success: IPA compiled.", result.returncode, result.stderr)


def generate_test_config(helper_binary_path, config_path, ports):
    command = Command(
        cmd=f"""
        {helper_binary_path} test-setup
        --output-dir {config_path}
        --ports {ports}
        """
    )
    result = command.run_blocking()
    process_result("Success: Test config created.", result.returncode, result.stderr)

    # HACK to move the public keys into <config_path>/pub
    # to match expected format on server
    config_path = Path(config_path)
    pub_key_dir_path = config_path / Path("pub")
    pub_key_dir_path.mkdir()
    for pub_key in itertools.chain(
        config_path.glob("*.pem"), config_path.glob("*.pub")
    ):
        pub_key.rename(pub_key_dir_path / pub_key.name)


def start_helper_process_cmd(
    helper_binary_path: Path,
    config_path: Path,
    role: Role,
) -> Command:
    identity = role.value
    network_config = Path(config_path) / Path("network.toml")
    helpers = load_helpers_from_network_config(network_config)
    helper = helpers[role]
    port = helper.helper_port
    cmd = f"""
    {helper_binary_path} --network {config_path}/network.toml
    --identity {identity} --tls-cert {config_path}/pub/h{identity}.pem
    --tls-key {config_path}/h{identity}.key --port {port}
    --mk-public-key {config_path}/pub/h{identity}_mk.pub
    --mk-private-key {config_path}/h{identity}_mk.key
    """
    return Command(cmd)


def start_helper(helper_binary_path, config_path, identity):
    role = Role(int(identity))
    command = start_helper_process_cmd(helper_binary_path, config_path, role)
    command.run_blocking()


def setup_helper(
    commit_hash: str,
    local_ipa_path: Path,
    config_path: Path,
    target_path: Path,
    helper_binary_path: Path,
    isolated: bool,
    ports: list[int],
):
    clone(local_ipa_path=local_ipa_path, exists_ok=not isolated)
    checkout_commit(local_ipa_path=local_ipa_path, commit_hash=commit_hash)

    if helper_binary_path.exists():
        if isolated:
            process_result(
                "", 1, f"Run in isolated mode and {helper_binary_path=} exists."
            )
        else:
            pass
    else:
        compile_(
            local_ipa_path,
            target_path,
            "helper",
            "web-app real-world-infra compact-gate stall-detection",
            default_features=False,
        )

    if config_path.exists():
        if isolated:
            shutil.rmtree(config_path)
            config_path.mkdir(parents=True)
            generate_test_config(
                helper_binary_path=helper_binary_path,
                config_path=config_path,
                ports=ports,
            )
    else:
        config_path.mkdir(parents=True)
        generate_test_config(
            helper_binary_path=helper_binary_path,
            config_path=config_path,
            ports=ports,
        )


def setup_coordinator(
    commit_hash: str,
    local_ipa_path: Path,
    target_path: Path,
    report_collector_binary_path: Path,
    isolated: bool,
):
    clone(local_ipa_path=local_ipa_path, exists_ok=not isolated)
    checkout_commit(local_ipa_path=local_ipa_path, commit_hash=commit_hash)

    if report_collector_binary_path.exists():
        if isolated:
            process_result(
                "",
                1,
                f"Run in isolated mode and {report_collector_binary_path=} exists.",
            )
        else:
            pass
    else:
        compile_(
            local_ipa_path,
            target_path,
            "report_collector",
            "clap cli test-fixture",
            default_features=True,
        )


def start_helper_sidecar_cmd(role: Role, config_path: Path) -> Command:
    network_config = Path(config_path) / Path("network.toml")
    helpers = load_helpers_from_network_config(network_config)
    helper = helpers[role]
    cmd = "uvicorn sidecar.app.main:app"
    env = {
        **os.environ,
        "ROLE": str(role.value),
        "ROOT_PATH": f"tmp/sidecar/{role.value}",
        "CONFIG_PATH": config_path,
        "UVICORN_PORT": str(helper.sidecar_port),
    }
    return Command(cmd=cmd, env=env)


def start_helper_sidecar(identity: int, config_path: Path):
    role = Role(int(identity))
    command = start_helper_sidecar_cmd(role, config_path)
    command.run_blocking()


def start_commands_parallel(commands: list[Command]):
    with PopenContextManager(
        commands, popen_args={"stdout": subprocess.PIPE, "text": True}
    ) as processes:
        for process in processes:
            process.wait()


def start_all_helper_sidecar_local_commands(config_path: Path):
    network_config = Path(config_path) / Path("network.toml")
    helpers = load_helpers_from_network_config(network_config)
    return [
        start_helper_sidecar_cmd(helper.role, config_path)
        for helper in helpers.values()
    ]


def start_all_helper_sidecar_local(config_path: Path):
    commands = start_all_helper_sidecar_local_commands(config_path)
    start_commands_parallel(commands)


def start_local_dev(config_path: Path):
    command = Command(cmd="npm --prefix server install")
    command.run_blocking()

    command = Command(cmd="npm --prefix server run dev")
    commands = [command] + start_all_helper_sidecar_local_commands(config_path)
    start_commands_parallel(commands)


def generate_test_data(
    size: int,
    max_breakdown_key: int,
    max_trigger_value: int,
    test_data_path: Path,
    report_collector_binary_path: Path,
):
    test_data_path.mkdir(exist_ok=True, parents=True)
    output_file = test_data_path / Path(f"events-{size}.txt")
    command = Command(
        cmd=f"""
    {report_collector_binary_path} gen-ipa-inputs -n {size}
    --max-breakdown-key {max_breakdown_key} --report-filter all
    --max-trigger-value {max_trigger_value} --seed 123
    """
    )
    with PopenContextManager(
        [command], popen_args={"stdout": subprocess.PIPE, "text": True}
    ) as processes:
        process = processes[0]
        command_output, _ = process.communicate()
        with open(output_file, "w", encoding="utf8") as output:
            output.write(command_output)

    process_result("Success: Test data created.", process.returncode, process.stderr)
    return output_file


async def wait_for_status(helper_url, query_id):
    url = urlunparse(helper_url._replace(scheme="ws", path=f"/ws/status/{query_id}"))
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

            print(f"Current status for {url=}: {status_data.get('status')}")

            # Add a delay before checking again
            await asyncio.sleep(1)


async def wait_for_helpers(helper_urls, query_id):
    tasks = [asyncio.create_task(wait_for_status(url, query_id)) for url in helper_urls]
    completed, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    for task in completed:
        task.result()
    return


async def start_ipa(
    config_path: Path,
    test_data_file: Path,
    report_collector_binary_path: Path,
    max_breakdown_key: int,
    per_user_credit_cap: int,
    query_id=None,
):
    network_config = Path(config_path) / Path("network.toml")
    helpers = load_helpers_from_network_config(network_config)
    if query_id:
        helper_urls = [
            helper.sidecar_url
            for helper in helpers.values()
            if helper != Role.COORDINATOR
        ]
        await wait_for_helpers(helper_urls, query_id)

    command = Command(
        cmd=f"""
    {report_collector_binary_path} --network {network_config}
    --input-file {test_data_file} oprf-ipa --max-breakdown-key {max_breakdown_key}
    --per-user-credit-cap {per_user_credit_cap} --plaintext-match-keys
    """
    )
    result = command.run_blocking()

    process_result("Success: IPA complete.", result.returncode, result.stderr)


def cleanup(local_ipa_path):
    local_ipa_path = Path(local_ipa_path)
    shutil.rmtree(local_ipa_path)
    click.echo(f"IPA removed from {local_ipa_path}")
