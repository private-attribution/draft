import asyncio
from dataclasses import dataclass, field
from enum import Enum, member
from functools import wraps
from pathlib import Path
import time
from typing import Optional
import click
import click_pathlib
from . import commands


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


class Option(Enum):
    LOCAL_IPA_PATH = member(
        click.option("--local_ipa_path", type=click_pathlib.Path(), default=None)
    )

    LOCAL_IPA_PATH_EXISTS = member(
        click.option(
            "--local_ipa_path", type=click_pathlib.Path(exists=True), default=None
        )
    )
    LOCAL_IPA_PATH_NOT_EXISTS = member(
        click.option(
            "--local_ipa_path", type=click_pathlib.Path(exists=False), default=None
        )
    )
    BRANCH = member(
        click.option("--branch", type=str, default="main", show_default=True)
    )
    COMMIT_HASH = member(click.option("--commit_hash", type=str, default=None))
    CONFIG_PATH = member(
        click.option(
            "--config_path", type=click_pathlib.Path(), default=None, show_default=True
        )
    )
    CONFIG_PATH_EXISTS = member(
        click.option(
            "--config_path",
            type=click_pathlib.Path(exists=True),
            default=None,
            show_default=True,
        )
    )
    CONFIG_PATH_NOT_EXISTS = member(
        click.option(
            "--config_path",
            type=click_pathlib.Path(exists=False),
            default=None,
            show_default=True,
        )
    )
    MAX_BREAKDOWN_KEY = member(
        click.option(
            "--max-breakdown-key",
            type=int,
            required=False,
            default=256,
            show_default=True,
        )
    )
    MAX_TRIGGER_VALUE = member(
        click.option(
            "--max-trigger-value",
            type=int,
            required=False,
            default=7,
            show_default=True,
        )
    )

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)


@dataclass
class Paths:
    branch: str
    commit_hash: str
    repo_path: Path
    config_path: Optional[Path] = None
    test_data_path: Optional[Path] = None
    target_path: Optional[Path] = field(init=False, default=None)
    helper_binary_path: Optional[Path] = field(init=False, default=None)
    report_collector_binary_path: Optional[Path] = field(init=False, default=None)

    def __post_init__(self):
        if not self.config_path:
            self.config_path = self.repo_path / Path("test_data/config")
        else:
            self.config_path = Path(self.config_path)
        if not self.test_data_path:
            self.test_data_path = self.repo_path / Path("test_data/input")
        else:
            self.test_data_path = Path(self.test_data_path)
        if self.branch and not self.commit_hash:
            self.commit_hash = commands.get_branch_commit_hash(
                self.repo_path, self.branch
            )
        if self.commit_hash:
            self.target_path = self.repo_path / Path(f"target-{self.commit_hash}")
            self.helper_binary_path = self.target_path / Path("release/helper")
            self.report_collector_binary_path = self.target_path / Path(
                "release/report_collector"
            )


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
    commands._clone(local_ipa_path, exists_ok)


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
@click.argument("branch", type=str, required=True, default="main")
def checkout_branch(local_ipa_path, branch):
    commands._checkout_branch(local_ipa_path=local_ipa_path, branch=branch)


@cli.command("compile")
@Option.BRANCH
@Option.COMMIT_HASH
@Option.LOCAL_IPA_PATH_EXISTS
def compile_command(
    branch: str,
    commit_hash: str,
    local_ipa_path: Path,
):
    paths = Paths(
        repo_path=local_ipa_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    if paths.target_path is None:
        raise Exception(
            f"Cannot compile without target directory specified. "
            f"Maybe {branch=} or {commit_hash=} are unset."
        )
    commands._compile(local_ipa_path=paths.repo_path, target_path=paths.target_path)


@cli.command()
@Option.BRANCH
@Option.COMMIT_HASH
@Option.LOCAL_IPA_PATH_EXISTS
@Option.CONFIG_PATH_NOT_EXISTS
def generate_test_config(
    branch: str,
    commit_hash: str,
    local_ipa_path: Path,
    config_path: Path,
):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    commands._generate_test_config(paths.helper_binary_path, paths.config_path)


@cli.command()
@Option.BRANCH
@Option.COMMIT_HASH
@Option.LOCAL_IPA_PATH_EXISTS
@Option.CONFIG_PATH_EXISTS
@click.argument("identity")
def start_helper(branch, commit_hash, local_ipa_path, config_path, identity):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    commands._start_helper(paths.helper_binary_path, paths.config_path, identity)


@cli.command()
@Option.BRANCH
@Option.COMMIT_HASH
@Option.LOCAL_IPA_PATH
@Option.CONFIG_PATH
@click.option(
    "--isolated/--repeatable",
    default=True,
    help="""
    Isolated expects repo to not exist, and will clean it up at completion.
    Repeatable will not cleanup, and will not write new files that aren't required.""",
)
def setup_helper(
    branch: str,
    commit_hash: str,
    local_ipa_path: Path,
    config_path: Path,
    isolated: bool,
):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    commands._setup_helper(
        commit_hash,
        paths.repo_path,
        paths.config_path,
        paths.target_path,
        paths.helper_binary_path,
        isolated,
    )


@cli.command()
@Option.BRANCH
@Option.COMMIT_HASH
@Option.LOCAL_IPA_PATH
@Option.CONFIG_PATH
@click.option(
    "--isolated/--repeatable",
    default=True,
    help="""
    Isolated expects repo to not exist, and will clean it up at completion.
    Repeatable will not cleanup, and will not write new files that aren't required.""",
)
def setup_coordinator(
    branch: str,
    commit_hash: str,
    local_ipa_path: Path,
    config_path: Path,
    isolated: bool,
):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    commands._setup_coordinator(
        commit_hash,
        paths.repo_path,
        paths.target_path,
        paths.report_collector_binary_path,
        isolated,
    )


@cli.command()
@Option.BRANCH
@Option.COMMIT_HASH
@Option.LOCAL_IPA_PATH_NOT_EXISTS
@Option.CONFIG_PATH_NOT_EXISTS
@click.argument("identity")
def start_isolated_helper(branch, commit_hash, local_ipa_path, config_path, identity):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    commands._setup_helper(
        commit_hash,
        paths.repo_path,
        paths.config_path,
        paths.target_path,
        paths.helper_binary_path,
        True,
    )
    commands._start_helper(
        paths.helper_binary_path,
        paths.config_path,
        identity,
    )


@cli.command
@click.argument("identity")
def start_helper_sidecar(identity):
    commands._start_helper_sidecar(identity)


@cli.command
def start_all_helper_sidecar_local():
    commands._start_all_helper_sidecar_local()


@cli.command
def start_local_dev():
    commands._start_local_dev()


@cli.command()
@Option.BRANCH
@Option.COMMIT_HASH
@click.option("--size", type=int, default=1000)
@Option.MAX_BREAKDOWN_KEY
@Option.MAX_TRIGGER_VALUE
@click.option("--test_data_path", type=click_pathlib.Path(), default=None)
@Option.LOCAL_IPA_PATH_EXISTS
def generate_test_data(
    branch: str,
    commit_hash: str,
    size: int,
    max_breakdown_key: int,
    max_trigger_value: int,
    test_data_path: Path,
    local_ipa_path: Path,
):
    paths = Paths(
        repo_path=local_ipa_path,
        test_data_path=test_data_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    commands._generate_test_data(
        size,
        max_breakdown_key,
        max_trigger_value,
        paths.test_data_path,
        paths.repo_path,
        paths.report_collector_binary_path,
    )


@cli.command()
@coro
@Option.BRANCH
@Option.COMMIT_HASH
@Option.LOCAL_IPA_PATH_NOT_EXISTS
@Option.MAX_BREAKDOWN_KEY
@Option.MAX_TRIGGER_VALUE
@click.option("--per-user-credit-cap", required=False, type=int, default=16)
@Option.CONFIG_PATH
@click.option("--size", type=int, default=1000)
@click.option("--test_data_path", type=click_pathlib.Path(), default=None)
async def start_isolated_ipa(
    branch,
    commit_hash,
    local_ipa_path,
    max_breakdown_key,
    max_trigger_value,
    per_user_credit_cap,
    config_path,
    size,
    test_data_path,
):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    commands._setup_helper(
        branch,
        commit_hash,
        paths.repo_path,
        paths.config_path,
        paths.target_path,
        paths.helper_binary_path,
        True,
    )
    test_data_file = commands._generate_test_data(
        size,
        max_breakdown_key,
        max_trigger_value,
        paths.test_data_path,
        paths.repo_path,
        paths.report_collector_binary_path,
    )
    await commands._start_ipa(
        paths.repo_path,
        paths.config_path,
        test_data_file,
        paths.report_collector_binary_path,
        max_breakdown_key,
        per_user_credit_cap,
    )


@cli.command()
@coro
@Option.LOCAL_IPA_PATH_EXISTS
@Option.BRANCH
@Option.COMMIT_HASH
@Option.MAX_BREAKDOWN_KEY
@click.option("--per-user-credit-cap", required=False, type=int, default=16)
@Option.CONFIG_PATH_EXISTS
@click.option(
    "--test_data_file",
    required=True,
    type=click_pathlib.Path(exists=True),
    default=None,
)
@click.option("--query_id", required=True, type=str, default=None)
async def start_ipa(
    local_ipa_path: Path,
    branch: str,
    commit_hash: str,
    max_breakdown_key: int,
    per_user_credit_cap: int,
    config_path: Path,
    test_data_file: Path,
    query_id: str,
):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        branch=branch,
        commit_hash=commit_hash,
    )
    local_ipa_path, config_path = paths.repo_path, paths.config_path
    await commands._start_ipa(
        paths.repo_path,
        paths.config_path,
        test_data_file,
        paths.report_collector_binary_path,
        max_breakdown_key,
        per_user_credit_cap,
        query_id,
    )


@cli.command()
@Option.LOCAL_IPA_PATH_EXISTS
def cleanup(local_ipa_path):
    commands._cleanup(local_ipa_path)


@cli.command()
@coro
@Option.LOCAL_IPA_PATH
@Option.BRANCH
@Option.COMMIT_HASH
@Option.CONFIG_PATH
@click.option(
    "--test_data_path", type=click_pathlib.Path(), default=None, show_default=True
)
@click.option("--size", type=int, default=1000, show_default=True)
@Option.MAX_BREAKDOWN_KEY
@Option.MAX_TRIGGER_VALUE
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
    commit_hash,
    config_path,
    test_data_path,
    size,
    max_breakdown_key,
    max_trigger_value,
    per_user_credit_cap,
    isolated,
):
    paths = Paths(
        repo_path=local_ipa_path,
        config_path=config_path,
        test_data_path=test_data_path,
        branch=branch,
        commit_hash=commit_hash,
    )

    commands._setup_helper(
        branch,
        commit_hash,
        paths.repo_path,
        paths.config_path,
        paths.target_path,
        paths.helper_binary_path,
        isolated,
    )

    test_data_file = commands._generate_test_data(
        size,
        max_breakdown_key,
        max_trigger_value,
        paths.test_data_path,
        paths.repo_path,
        paths.report_collector_binary_path,
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
            paths.repo_path,
            paths.config_path,
            test_data_file,
            paths.report_collector_binary_path,
            max_breakdown_key,
            per_user_credit_cap,
        )

    if isolated:
        commands._cleanup(local_ipa_path)


if __name__ == "__main__":
    cli()
