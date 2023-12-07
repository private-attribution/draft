import itertools
from pathlib import Path
import subprocess
import shlex
import shutil
import time
import click


helper_ports = {
    1: 7431,
    2: 7432,
    3: 7433,
}

DEFAULT_IPA_PATH = Path("ipa")
DEFAULT_CONFIG_PATH = DEFAULT_IPA_PATH / Path("test_data/config")
DEFAULT_TEST_DATA = DEFAULT_IPA_PATH / Path("test_data/input")


def echo_success(success_msg, returncode):
    if returncode == 0:
        click.echo(click.style(success_msg, fg="green"))
    else:
        click.echo(click.style("Failure!", blink=True, bold=True, bg="red", fg="white"))
        raise Exception("Process failed")


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--local_ipa_path", type=click.Path(exists=False), default=DEFAULT_IPA_PATH
)
def clone(local_ipa_path):
    cmd = f"git clone https://github.com/private-attribution/ipa.git {local_ipa_path}"
    result = subprocess.run(shlex.split(cmd))
    echo_success("Success: IPA cloned.", result.returncode)


@cli.command()
@click.argument("branch", type=str, required=True, default="main")
def checkout_branch(branch):
    cmd = "git -C ipa fetch --all"
    result = subprocess.run(shlex.split(cmd))
    echo_success("Success: upstream fetched.", result.returncode)
    cmd = f"git -C ipa checkout {branch}"
    result = subprocess.run(shlex.split(cmd))
    echo_success(f"Success: {branch} checked out.", result.returncode)
    cmd = "git -C ipa pull"
    result = subprocess.run(shlex.split(cmd))
    echo_success("Success: fast forwarded.", result.returncode)


@cli.command("compile")
@click.option("--setcap/--no-setcap", default=False)
def _compile(setcap):
    cmd = """
    cargo build --bin helper --manifest-path=ipa/Cargo.toml
    --no-default-features
    --features="web-app real-world-infra compact-gate stall-detection"
    --release
    """
    result = subprocess.run(shlex.split(cmd))
    echo_success("Success: IPA compiled.", result.returncode)
    if setcap:
        cmd = "sudo setcap CAP_NET_BIND_SERVICE=+eip target/release/helper"
        result = subprocess.run(shlex.split(cmd))
        echo_success("Success: setcap set.", result.returncode)


@cli.command()
@click.option(
    "--local_ipa_path", type=click.Path(exists=False), default=DEFAULT_IPA_PATH
)
@click.option(
    "--config_path", type=click.Path(exists=False), default=DEFAULT_CONFIG_PATH
)
def generate_test_config(local_ipa_path, config_path):
    cmd = f"""
    {local_ipa_path}/target/release/helper test-setup
    --output-dir {config_path}
    --ports {" ".join(str(p) for p in helper_ports.values())}
    """
    result = subprocess.run(shlex.split(cmd))
    echo_success("Success: Test config created.", result.returncode)

    # HACK to move the public keys into <config_path>/pub
    # to match expected format on server
    config_path = Path(config_path)
    pub_key_dir_path = config_path / Path("pub")
    pub_key_dir_path.mkdir()
    for pub_key in itertools.chain(
        config_path.glob("*.pem"), config_path.glob("*.pub")
    ):
        pub_key.rename(pub_key_dir_path / pub_key.name)


def _start_helper_process(local_ipa_path, config_path, identity):
    port = helper_ports[int(identity)]
    cmd = f"""
    {local_ipa_path}/target/release/helper --network {config_path}/network.toml
    --identity {identity} --tls-cert {config_path}/pub/h{identity}.pem
    --tls-key {config_path}/h{identity}.key --port {port}
    --mk-public-key {config_path}/pub/h{identity}_mk.pub
    --mk-private-key {config_path}/h{identity}_mk.key
    """
    return subprocess.Popen(shlex.split(cmd))


@cli.command()
@click.option(
    "--local_ipa_path", type=click.Path(exists=False), default=DEFAULT_IPA_PATH
)
@click.option(
    "--config_path", type=click.Path(exists=True), default=DEFAULT_CONFIG_PATH
)
@click.argument("identity")
def start_helper(local_ipa_path, config_path, identity):
    process = _start_helper_process(config_path, identity)
    process.wait()


@cli.command()
@click.option("--size", type=int, default=1000)
@click.option("--test_data_path", type=click.Path(), default=DEFAULT_TEST_DATA)
def generate_test_data(size, test_data_path):
    test_data_path = Path(test_data_path)
    test_data_path.mkdir(exist_ok=True)
    output_file = test_data_path / Path(f"events-{size}.txt")
    cmd = f"""
    cargo run --manifest-path=ipa/Cargo.toml --release --bin report_collector
    --features="clap cli test-fixture" -- gen-ipa-inputs -n {size}
    --max-breakdown-key 256 --report-filter all --max-trigger-value 7 --seed 123
    """
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, text=True)
    command_output, _ = process.communicate()
    with open(output_file, "w") as output:
        output.write(command_output)

    echo_success("Success: Test data created.", process.returncode)
    return output_file


@cli.command()
@click.option(
    "--local_ipa_path", type=click.Path(exists=False), default=DEFAULT_IPA_PATH
)
@click.option("--max-breakdown-key", required=False, type=int, default=256)
@click.option("--per-user-credit-cap", required=False, type=int, default=16)
@click.option(
    "--config_path", type=click.Path(exists=True), default=DEFAULT_CONFIG_PATH
)
@click.argument("test_data_file", type=click.Path(exists=True))
def start_ipa(
    local_ipa_path, max_breakdown_key, per_user_credit_cap, config_path, test_data_file
):
    network_file = Path(config_path) / Path("network.toml")
    cmd = f"""
    ipa/target/release/report_collector --network {network_file}
    --input-file {test_data_file} oprf-ipa --max-breakdown-key {max_breakdown_key}
    --per-user-credit-cap {per_user_credit_cap} --plaintext-match-keys
    """
    result = subprocess.run(shlex.split(cmd))
    echo_success("Success: IPA complete.", result.returncode)


@cli.command()
@click.option(
    "--local_ipa_path", type=click.Path(exists=False), default=DEFAULT_IPA_PATH
)
def cleanup(local_ipa_path):
    local_ipa_path = Path(local_ipa_path)
    shutil.rmtree(local_ipa_path)
    click.echo("IPA removed")


@cli.command()
@click.option(
    "--local_ipa_path", type=click.Path(exists=False), default=DEFAULT_IPA_PATH
)
@click.option("--branch", type=str, default="main", show_default=True)
@click.option(
    "--config_path",
    type=click.Path(exists=False),
    default=DEFAULT_CONFIG_PATH,
    show_default=True,
)
@click.option(
    "--test_data_path",
    type=click.Path(exists=False),
    default=DEFAULT_TEST_DATA,
    show_default=True,
)
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
@click.pass_context
def demo_ipa(
    ctx,
    local_ipa_path,
    branch,
    config_path,
    test_data_path,
    size,
    max_breakdown_key,
    per_user_credit_cap,
    isolated,
):
    # setup
    if isolated:
        if local_ipa_path.exists():
            click.echo(
                click.style("Failure!", blink=True, bold=True, bg="red", fg="white")
            )
            click.echo(
                click.style(
                    f"Run in isolated mode and {local_ipa_path=} exists.",
                    bold=True,
                    bg="red",
                    fg="white",
                )
            )
            raise SystemExit(1)
        else:
            ctx.invoke(clone)
    else:
        if not local_ipa_path.exists():
            ctx.invoke(clone)

    ctx.invoke(checkout_branch, branch=branch)

    helper_binary_path = local_ipa_path / Path("target/release/helper")

    if isolated or not helper_binary_path.exists():
        ctx.invoke(_compile, setcap=False)

    if config_path.exists():
        if isolated:
            click.echo(
                click.style("Failure!", blink=True, bold=True, bg="red", fg="white")
            )
            click.echo(
                click.style(
                    f"Run in isolated mode and {config_path=} exists.",
                    bold=True,
                    bg="red",
                    fg="white",
                )
            )
            raise SystemExit(1)
        else:
            shutil.rmtree(config_path)

    config_path.mkdir(parents=True)

    ctx.invoke(generate_test_config, config_path=config_path)

    test_data_file = ctx.invoke(
        generate_test_data, size=size, test_data_path=test_data_path
    )

    # run ipa
    h1_process = _start_helper_process(local_ipa_path, config_path, 1)
    h2_process = _start_helper_process(local_ipa_path, config_path, 2)
    h3_process = _start_helper_process(local_ipa_path, config_path, 3)

    # allow helpers to start
    time.sleep(3)
    ctx.invoke(
        start_ipa,
        max_breakdown_key=max_breakdown_key,
        per_user_credit_cap=per_user_credit_cap,
        test_data_file=test_data_file,
        config_path=config_path,
    )

    # cleanup
    h1_process.kill()
    h2_process.kill()
    h3_process.kill()

    if isolated:
        ctx.invoke(cleanup)


if __name__ == "__main__":
    cli()
