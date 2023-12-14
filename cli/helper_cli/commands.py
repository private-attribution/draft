import asyncio
from dataclasses import dataclass, field
from enum import Enum
import itertools
import json
import os
from pathlib import Path
import subprocess
import shlex
import shutil
import tomllib
from typing import Optional
from urllib.parse import urlparse, urlunparse
import click
import websockets


class Role(int, Enum):
    COORDINATOR = 0
    HELPER_1 = 1
    HELPER_2 = 2
    HELPER_3 = 3


@dataclass
class Helper:
    role: Role
    sidecar_port: int
    helper_port: Optional[int] = None


helpers: dict[Role, Helper] = {
    Role.COORDINATOR: Helper(role=Role.COORDINATOR, sidecar_port=17430),
    Role.HELPER_1: Helper(role=Role.HELPER_1, helper_port=7431, sidecar_port=17431),
    Role.HELPER_2: Helper(role=Role.HELPER_2, helper_port=7432, sidecar_port=17432),
    Role.HELPER_3: Helper(role=Role.HELPER_3, helper_port=7433, sidecar_port=17433),
}


@dataclass
class Command:
    cmd: str
    env: Optional[dict] = field(default_factory=lambda: {**os.environ})

    def run_blocking(self):
        return subprocess.run(shlex.split(self.cmd), env=self.env)


def process_result(success_msg, returncode, failure_message=None):
    if returncode == 0:
        click.echo(click.style(success_msg, fg="green"))
    else:
        click.echo(click.style("Failure!", blink=True, bold=True, bg="red", fg="white"))
        if failure_message is not None:
            click.echo(click.style(failure_message, bold=True, bg="red", fg="white"))
        raise SystemExit(1)


class PopenContextManager:
    def __init__(self, commands: list[Command], Popen_args=None):
        self.commands = commands
        if Popen_args is not None:
            self.Popen_args = Popen_args
        else:
            self.Popen_args = {}

    def __enter__(self):
        self.processes = []
        for command in self.commands:
            process = subprocess.Popen(
                shlex.split(command.cmd), env=command.env, **self.Popen_args
            )
            self.processes.append(process)
        return self.processes

    def __exit__(self, exc_type, exc_value, exc_tb):
        for process in self.processes:
            process.kill()


def _clone(local_ipa_path, exists_ok):
    # setup
    if local_ipa_path.exists():
        if exists_ok:
            process_result(f"{local_ipa_path=} exists. Skipping clone.", 0)
            return
        else:
            process_result("", 1, f"Run in isolated mode and {local_ipa_path=} exists.")

    command = Command(
        cmd=f"git clone https://github.com/private-attribution/ipa.git {local_ipa_path}"
    )
    result = command.run_blocking()
    process_result("Success: IPA cloned.", result.returncode)


def _checkout_branch(branch):
    command = Command(cmd="git -C ipa fetch --all")
    result = command.run_blocking()
    process_result("Success: upstream fetched.", result.returncode)
    command = Command(cmd=f"git -C ipa checkout {branch}")
    result = command.run_blocking()
    process_result(f"Success: {branch} checked out.", result.returncode)
    command = Command(cmd="git -C ipa pull")
    result = command.run_blocking()
    process_result("Success: fast forwarded.", result.returncode)


def _compile(local_ipa_path):
    manifest_path = local_ipa_path / Path("Cargo.toml")
    command = Command(
        cmd=f"""cargo build --bin helper --manifest-path={manifest_path}
        --no-default-features --features="web-app real-world-infra
        compact-gate stall-detection" --release"""
    )
    result = command.run_blocking()
    process_result("Success: IPA compiled.", result.returncode)


def _generate_test_config(local_ipa_path, config_path):
    command = Command(
        cmd=f"""
    {local_ipa_path}/target/release/helper test-setup
    --output-dir {config_path}
    --ports {" ".join(str(helper.helper_port) for helper in helpers.values())}
    """
    )
    result = command.run_blocking()
    process_result("Success: Test config created.", result.returncode)

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
    local_ipa_path: Path, config_path: Path, role: Role
) -> Command:
    identity = role.value
    helper = helpers[role]
    port = helper.helper_port
    cmd = f"""
    {local_ipa_path}/target/release/helper --network {config_path}/network.toml
    --identity {identity} --tls-cert {config_path}/pub/h{identity}.pem
    --tls-key {config_path}/h{identity}.key --port {port}
    --mk-public-key {config_path}/pub/h{identity}_mk.pub
    --mk-private-key {config_path}/h{identity}_mk.key
    """
    return Command(cmd)


def _start_helper(local_ipa_path, config_path, identity):
    role = Role(int(identity))
    command = start_helper_process_cmd(local_ipa_path, config_path, role)
    command.run_blocking()


def _setup_helper(branch, local_ipa_path, config_path, isolated):
    _clone(local_ipa_path=local_ipa_path, exists_ok=(not isolated))
    _checkout_branch(branch=branch)

    helper_binary_path = local_ipa_path / Path("target/release/helper")

    if helper_binary_path.exists():
        if isolated:
            process_result(
                "", 1, f"Run in isolated mode and {helper_binary_path=} exists."
            )
        else:
            pass
    else:
        _compile(local_ipa_path)

    if config_path.exists():
        if isolated:
            process_result("", 1, f"Run in isolated mode and {config_path=} exists.")
        else:
            shutil.rmtree(config_path)

    config_path.mkdir(parents=True)

    _generate_test_config(local_ipa_path=local_ipa_path, config_path=config_path)


def start_helper_sidecar_cmd(role: Role) -> Command:
    helper = helpers[role]
    cmd = "uvicorn runner.app.main:app"
    env = {
        **os.environ,
        "ROLE": str(role.value),
        "ROOT_PATH": f"tmp/runner/{role.value}",
        "UVICORN_PORT": str(helper.sidecar_port),
    }
    return Command(cmd=cmd, env=env)


def _start_helper_sidecar(identity):
    role = Role(int(identity))
    command = start_helper_sidecar_cmd(role)
    command.run_blocking()


def _generate_test_data(size, test_data_path):
    test_data_path.mkdir(exist_ok=True)
    output_file = test_data_path / Path(f"events-{size}.txt")
    command = Command(
        cmd=f"""
    cargo run --manifest-path=ipa/Cargo.toml --release --bin report_collector
    --features="clap cli test-fixture" -- gen-ipa-inputs -n {size}
    --max-breakdown-key 256 --report-filter all --max-trigger-value 7 --seed 123
    """
    )
    with PopenContextManager(
        [command], Popen_args={"stdout": subprocess.PIPE, "text": True}
    ) as processes:
        process = processes[0]
        command_output, _ = process.communicate()
        with open(output_file, "w") as output:
            output.write(command_output)

    process_result("Success: Test data created.", process.returncode)
    return output_file


async def wait_for_status(helper_url, job_id):
    url = urlunparse(helper_url._replace(scheme="ws", path=f"/ws/status/{job_id}"))
    async with websockets.connect(url) as websocket:
        while True:
            status_json = await websocket.recv()
            status_data = json.loads(status_json)
            status = status_data.get("status")
            match status:
                case "running":
                    return
                case "not-found":
                    raise Exception(f"{job_id=} doesn't exists.")

            print(f"Current status for {url=}: {status_data.get('status')}")

            # Add a delay before checking again
            await asyncio.sleep(1)


async def wait_for_helpers(helper_urls, job_id):
    tasks = [
        asyncio.create_task(wait_for_status(url, "running")) for url in helper_urls
    ]
    completed, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    for task in completed:
        task.result()
    return


async def _start_ipa(
    local_ipa_path,
    max_breakdown_key,
    per_user_credit_cap,
    config_path,
    test_data_file,
    job_id,
):
    network_file = Path(config_path) / Path("network.toml")
    with open(network_file, "rb") as f:
        network_data = tomllib.load(f)
    network_file_urls = [
        urlparse(f"http://{peer['url']}") for peer in network_data["peers"]
    ]
    helper_urls = [
        url._replace(netloc=f"{url.hostname}:{url.port+10000}")
        for url in network_file_urls
    ]
    await wait_for_helpers(helper_urls, job_id)

    command = Command(
        cmd=f"""
    ipa/target/release/report_collector --network {network_file}
    --input-file {test_data_file} oprf-ipa --max-breakdown-key {max_breakdown_key}
    --per-user-credit-cap {per_user_credit_cap} --plaintext-match-keys
    """
    )
    result = command.run_blocking()
    process_result("Success: IPA complete.", result.returncode)


def _cleanup(local_ipa_path):
    local_ipa_path = Path(local_ipa_path)
    shutil.rmtree(local_ipa_path)
    click.echo(f"IPA removed from {local_ipa_path}")
