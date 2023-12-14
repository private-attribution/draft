import asyncio
from dataclasses import dataclass
from enum import Enum, member
from functools import wraps
from pathlib import Path
import subprocess
import time
from typing import Optional
import click
from . import commands


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


class Option(Enum):
    LOCAL_IPA_PATH = member(
        click.option("--local_ipa_path", type=click.Path(), default=None)
    )

    LOCAL_IPA_PATH_EXISTS = member(
        click.option("--local_ipa_path", type=click.Path(exists=True), default=None)
    )
    LOCAL_IPA_PATH_NOT_EXISTS = member(
        click.option("--local_ipa_path", type=click.Path(exists=False), default=None)
    )
    BRANCH = member(
        click.option("--branch", type=str, default="main", show_default=True)
    )
    CONFIG_PATH = member(
        click.option(
            "--config_path", type=click.Path(), default=None, show_default=True
        )
    )
    CONFIG_PATH_EXISTS = member(
        click.option(
            "--config_path",
            type=click.Path(exists=True),
            default=None,
            show_default=True,
        )
    )
    CONFIG_PATH_NOT_EXISTS = member(
        click.option(
            "--config_path",
            type=click.Path(exists=False),
            default=None,
            show_default=True,
        )
    )

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)


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


@click.group()
def cli():
    pass


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
    commands._clone(local_ipa_path, exists_ok)


@cli.command()
@click.argument("branch", type=str, required=True, default="main")
def checkout_branch(branch):
    commands._checkout_branch(branch)


@cli.command("compile")
@Option.LOCAL_IPA_PATH_EXISTS
def compile_command(local_ipa_path):
    local_ipa_path = Paths(repo_path=local_ipa_path).repo_path
    commands._compile(local_ipa_path)


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
@Option.CONFIG_PATH_NOT_EXISTS
def generate_test_config(local_ipa_path, config_path):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    commands._generate_test_config(local_ipa_path, config_path)


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
@Option.CONFIG_PATH_EXISTS
@click.argument("identity")
def start_helper(local_ipa_path, config_path, identity):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    commands._start_helper(local_ipa_path, config_path, identity)


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
    commands._setup_helper(branch, local_ipa_path, config_path, isolated)


@cli.command()
@Option.BRANCH
@Option.LOCAL_IPA_PATH_NOT_EXISTS
@Option.CONFIG_PATH_NOT_EXISTS
@click.argument("identity")
def start_isolated_helper(branch, local_ipa_path, config_path, identity):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    commands._setup_helper(branch, local_ipa_path, config_path, True)
    commands._start_helper(local_ipa_path, config_path, identity)


@cli.command
@click.argument("identity")
def start_helper_sidecar(identity):
    commands._start_helper_sidecar(identity)


@cli.command
def start_all_helper_sidecar_local():
    _commands = [
        commands.start_helper_sidecar_cmd(helper.role)
        for helper in commands.helpers.values()
    ]
    with commands.PopenContextManager(
        _commands, Popen_args={"stdout": subprocess.PIPE, "text": True}
    ) as processes:
        for process in processes:
            process.wait()


@cli.command()
@click.option("--size", type=int, default=1000)
@click.option("--test_data_path", type=click.Path(), default=None)
def generate_test_data(size, test_data_path):
    paths = Paths(test_data_path=test_data_path)
    test_data_path = paths.test_data_path

    commands._generate_test_data(size, test_data_path)


@cli.command()
@coro
@Option.BRANCH
@Option.LOCAL_IPA_PATH_NOT_EXISTS
@click.option("--max-breakdown-key", required=False, type=int, default=256)
@click.option("--per-user-credit-cap", required=False, type=int, default=16)
@Option.CONFIG_PATH
@click.option("--size", type=int, default=1000)
@click.option("--test_data_path", type=click.Path(), default=None)
async def start_isolated_ipa(
    branch,
    local_ipa_path,
    max_breakdown_key,
    per_user_credit_cap,
    config_path,
    size,
    test_data_path,
):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    commands._setup_helper(branch, local_ipa_path, config_path, True)
    test_data_file = commands._generate_test_data(
        size=size, test_data_path=test_data_path
    )
    await commands._start_ipa(
        local_ipa_path,
        max_breakdown_key,
        per_user_credit_cap,
        config_path,
        test_data_file,
    )


@cli.command()
@coro
@Option.LOCAL_IPA_PATH_EXISTS
@click.option("--max-breakdown-key", required=False, type=int, default=256)
@click.option("--per-user-credit-cap", required=False, type=int, default=16)
@Option.CONFIG_PATH_EXISTS
@click.option(
    "--test_data_file", required=True, type=click.Path(exists=True), default=None
)
@click.option("--job_id", required=True, type=str)
async def start_ipa(
    local_ipa_path,
    max_breakdown_key,
    per_user_credit_cap,
    config_path,
    test_data_file,
    job_id,
):
    paths = Paths(repo_path=local_ipa_path, config_path=config_path)
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    await commands._start_ipa(
        local_ipa_path,
        max_breakdown_key,
        per_user_credit_cap,
        config_path,
        test_data_file,
        job_id,
    )


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
def cleanup(local_ipa_path):
    local_ipa_path = Paths(repo_path=local_ipa_path).repo_path
    commands._cleanup(local_ipa_path)


@cli.command()
@coro
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
async def demo_ipa(
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

    commands._setup_helper(branch, local_ipa_path, config_path, isolated)

    test_data_file = commands._generate_test_data(
        size=size, test_data_path=test_data_path
    )

    _commands = [
        commands.start_helper_process_cmd(local_ipa_path, config_path, helper.role)
        for helper in commands.helpers.values()
    ]

    # run ipa
    with (commands.PopenContextManager(_commands),):
        # allow helpers to start
        time.sleep(3)
        await commands._start_ipa(
            local_ipa_path=local_ipa_path,
            max_breakdown_key=max_breakdown_key,
            per_user_credit_cap=per_user_credit_cap,
            test_data_file=test_data_file,
            config_path=config_path,
        )

    if isolated:
        commands._cleanup(local_ipa_path)


if __name__ == "__main__":
    cli()
