from dataclasses import dataclass, field
from enum import Enum, member
import itertools
import os
from pathlib import Path
import subprocess
import shlex
import shutil
import time
from typing import Optional
import click


class Role(int, Enum):
    COORDINATOR = 0
    HELPER_1 = 1
    HELPER_2 = 2
    HELPER_3 = 3


def option_wrapper(option):
    def wrapper(f):
        return option(f)

    return wrapper


class Option(Enum):
    LOCAL_IPA_PATH = member(
        option_wrapper(
            click.option("--local_ipa_path", type=click.Path(), default=None)
        )
    )
    LOCAL_IPA_PATH_EXISTS = member(
        option_wrapper(
            click.option("--local_ipa_path", type=click.Path(exists=True), default=None)
        )
    )
    LOCAL_IPA_PATH_NOT_EXISTS = member(
        option_wrapper(
            click.option(
                "--local_ipa_path", type=click.Path(exists=False), default=None
            )
        )
    )
    BRANCH = member(
        option_wrapper(
            click.option("--branch", type=str, default="main", show_default=True)
        )
    )
    CONFIG_PATH = member(
        option_wrapper(
            click.option(
                "--config_path", type=click.Path(), default=None, show_default=True
            )
        )
    )
    CONFIG_PATH_EXISTS = member(
        option_wrapper(
            click.option(
                "--config_path",
                type=click.Path(exists=True),
                default=None,
                show_default=True,
            )
        )
    )
    CONFIG_PATH_NOT_EXISTS = member(
        option_wrapper(
            click.option(
                "--config_path",
                type=click.Path(exists=False),
                default=None,
                show_default=True,
            )
        )
    )

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)


@dataclass
class Helper:
    role: Role
    helper_port: int
    sidecar_port: int


@dataclass
class Command:
    cmd: str
    env: Optional[dict] = field(default_factory=lambda: {**os.environ})

    def run_blocking(self):
        return subprocess.run(shlex.split(self.cmd), env=self.env)


helpers: dict[Role, Helper] = {
    Role.HELPER_1: Helper(role=Role.HELPER_1, helper_port=7431, sidecar_port=8431),
    Role.HELPER_2: Helper(role=Role.HELPER_2, helper_port=7432, sidecar_port=8432),
    Role.HELPER_3: Helper(role=Role.HELPER_3, helper_port=7433, sidecar_port=8433),
}


DEFAULT_IPA_PATH = Path("ipa")
DEFAULT_CONFIG_PATH = DEFAULT_IPA_PATH / Path("test_data/config")
DEFAULT_TEST_DATA = DEFAULT_IPA_PATH / Path("test_data/input")


@dataclass
class Paths:
    repo_path: Optional[Path] = None
    config_path: Optional[Path] = None
    test_data_path: Optional[Path] = None

    def __post_init__(self):
        if not self.repo_path:
            self.repo_path = Path("ipa")
        else:
            self.repo_path = Path(self.repo_path)
        if not self.config_path:
            self.config_path = self.repo_path / Path("test_data/config")
        else:
            self.config_path = Path(self.config_path)
        if not self.test_data_path:
            self.test_data_path = self.repo_path / Path("test_data/input")
        else:
            self.test_data_path = Path(self.test_data_path)


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


@click.group()
def cli():
    pass


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


@cli.command()
@Option.LOCAL_IPA_PATH
@click.option(
    "--exists-ok",
    is_flag=True,
    show_default=True,
    default=False,
    help="Prevent warning and skip if path exists.",
)
def clone(local_ipa_path, exists_ok):
    local_ipa_path = Paths(repo_path=local_ipa_path).repo_path
    _clone(local_ipa_path, exists_ok)


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


@cli.command()
@click.argument("branch", type=str, required=True, default="main")
def checkout_branch(branch):
    checkout_branch(branch)


def _compile(local_ipa_path):
    manifest_path = local_ipa_path / Path("Cargo.toml")
    command = Command(
        cmd=f"""cargo build --bin helper --manifest-path={manifest_path}
        --no-default-features --features="web-app real-world-infra
        compact-gate stall-detection" --release"""
    )
    result = command.run_blocking()
    process_result("Success: IPA compiled.", result.returncode)


@cli.command("compile")
@Option.LOCAL_IPA_PATH
def compile_command(local_ipa_path):
    local_ipa_path = Paths(repo_path=local_ipa_path).repo_path
    _compile(local_ipa_path)


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


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
@Option.CONFIG_PATH_NOT_EXISTS
def generate_test_config(local_ipa_path, config_path):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    _generate_test_config(local_ipa_path, config_path)


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


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
@Option.CONFIG_PATH_EXISTS
@click.argument("identity")
def start_helper(local_ipa_path, config_path, identity):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    _start_helper(local_ipa_path, config_path, identity)


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


@cli.command()
@Option.BRANCH
@Option.LOCAL_IPA_PATH
@Option.CONFIG_PATH
@click.option(
    "--isolated/--repeatable",
    default=True,
    help="""
    Isolated expects repo to not exist, and will clean it up at completion.
    Repeatable will not cleanup, and will not write new files that aren't required.""",
)
def setup_helper(branch, local_ipa_path, config_path, isolated):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    _setup_helper(branch, local_ipa_path, config_path, isolated)


@cli.command()
@Option.BRANCH
@Option.LOCAL_IPA_PATH_NOT_EXISTS
@Option.CONFIG_PATH_NOT_EXISTS
@click.argument("identity")
def start_isolated_helper(branch, local_ipa_path, config_path, identity):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    _setup_helper(branch, local_ipa_path, config_path, True)
    _start_helper(local_ipa_path, config_path, identity)


def start_helper_sidecar_cmd(role: Role) -> Command:
    helper = helpers[role]
    cmd = "uvicorn runner.app.main:app"
    env = {
        **os.environ,
        "ROLE": str(role.value),
        "UVICORN_PORT": str(helper.sidecar_port),
    }
    return Command(cmd=cmd, env=env)


def _start_helper_sidecar(identity):
    role = Role(int(identity))
    command = start_helper_sidecar_cmd(role)
    command.run_blocking()


@cli.command
@click.argument("identity")
def start_helper_sidecar(identity):
    _start_helper_sidecar(identity)


@cli.command
def start_all_helper_sidecar_local():
    commands = [start_helper_sidecar_cmd(helper.role) for helper in helpers.values()]
    with PopenContextManager(
        commands, Popen_args={"stdout": subprocess.PIPE, "text": True}
    ) as processes:
        for process in processes:
            process.wait()


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


@cli.command()
@click.option("--size", type=int, default=1000)
@click.option("--test_data_path", type=click.Path(), default=None)
def generate_test_data(size, test_data_path):
    paths = Paths(test_data_path=test_data_path)
    test_data_path = paths.test_data_path

    _generate_test_data(size, test_data_path)


def _start_ipa(
    local_ipa_path, max_breakdown_key, per_user_credit_cap, config_path, test_data_file
):
    network_file = Path(config_path) / Path("network.toml")
    command = Command(
        cmd=f"""
    ipa/target/release/report_collector --network {network_file}
    --input-file {test_data_file} oprf-ipa --max-breakdown-key {max_breakdown_key}
    --per-user-credit-cap {per_user_credit_cap} --plaintext-match-keys
    """
    )
    result = command.run_blocking()
    process_result("Success: IPA complete.", result.returncode)


@cli.command()
@Option.LOCAL_IPA_PATH_NOT_EXISTS
@click.option("--max-breakdown-key", required=False, type=int, default=256)
@click.option("--per-user-credit-cap", required=False, type=int, default=16)
@Option.CONFIG_PATH_EXISTS
@click.argument("test_data_file", type=click.Path(exists=True))
def start_ipa(
    local_ipa_path, max_breakdown_key, per_user_credit_cap, config_path, test_data_file
):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    _start_ipa(
        local_ipa_path,
        max_breakdown_key,
        per_user_credit_cap,
        config_path,
        test_data_file,
    )


def _cleanup(local_ipa_path):
    local_ipa_path = Path(local_ipa_path)
    shutil.rmtree(local_ipa_path)
    click.echo(f"IPA removed from {local_ipa_path}")


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
def cleanup(local_ipa_path):
    local_ipa_path = Paths(repo_path=local_ipa_path).repo_path
    _cleanup(local_ipa_path)


@cli.command()
@Option.LOCAL_IPA_PATH
@Option.BRANCH
@Option.CONFIG_PATH
@click.option("--test_data_path", type=click.Path(), default=None, show_default=True)
@click.option("--size", type=int, default=1000, show_default=True)
@click.option("--max-breakdown-key", type=int, default=256, show_default=True)
@click.option("--per-user-credit-cap", type=int, default=16, show_default=True)
@click.option(
    "--isolated/--repeatable",
    default=True,
    help="""
    Isolated expects repo to not exist, and will clean it up at completion.
    Repeatable will not cleanup, and will not write new files that aren't required.""",
)
def demo_ipa(
    local_ipa_path,
    branch,
    config_path,
    test_data_path,
    size,
    max_breakdown_key,
    per_user_credit_cap,
    isolated,
):
    paths = Paths(
        repo_path=local_ipa_path, config_path=config_path, test_data_path=test_data_path
    )
    local_ipa_path, config_path, test_data_path = (
        paths.repo_path,
        paths.config_path,
        paths.test_data_path,
    )

    _setup_helper(branch, local_ipa_path, config_path, isolated)

    test_data_file = _generate_test_data(size=size, test_data_path=test_data_path)

    commands = [
        start_helper_process_cmd(local_ipa_path, config_path, helper.role)
        for helper in helpers.values()
    ]

    # run ipa
    with (PopenContextManager(commands),):
        # allow helpers to start
        time.sleep(3)
        _start_ipa(
            local_ipa_path=local_ipa_path,
            max_breakdown_key=max_breakdown_key,
            per_user_credit_cap=per_user_credit_cap,
            test_data_file=test_data_file,
            config_path=config_path,
        )

    if isolated:
        _cleanup()


if __name__ == "__main__":
    cli()
