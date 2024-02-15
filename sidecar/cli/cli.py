import os
from pathlib import Path
from typing import Optional

import click
import click_pathlib

from ..app.command import Command, start_commands_parallel
from ..app.helpers import Role, load_helpers_from_network_config


@click.group()
def cli():
    pass


def start_helper_sidecar_command(
    config_path: Path,
    identity: int,
    root_path: Optional[Path] = None,
):
    role = Role(int(identity))
    network_config = config_path / Path("network.toml")
    root_path = root_path or Path(f"tmp/sidecar/{role.value}")
    root_path.mkdir(parents=True, exist_ok=True)
    helpers = load_helpers_from_network_config(network_config)
    if role == Role.COORDINATOR:
        private_key_pem_path = config_path / Path("coordinator.key")
    else:
        private_key_pem_path = config_path / Path(f"h{role.value}.key")
    helper = helpers[role]
    cmd = "uvicorn sidecar.app.main:app"
    env = {
        **os.environ,
        "ROLE": str(role.value),
        "ROOT_PATH": root_path,
        "CONFIG_PATH": config_path,
        "NETWORK_CONFIG_PATH": network_config,
        "PRIVATE_KEY_PEM_PATH": private_key_pem_path,
        "UVICORN_PORT": str(helper.sidecar_port),
        "UVICORN_HOST": "0.0.0.0",
    }
    return Command(cmd=cmd, env=env)


def start_traefik_command(
    config_path: Path,
    identity: int,
    root_path: Optional[Path] = None,
):
    role = Role(int(identity))
    root_path = root_path or Path(f"tmp/sidecar/{role.value}")
    if role == Role.COORDINATOR:
        base_domain = "coordinator.ipa-helper.dev"
    else:
        base_domain = f"helper{role.value}.ipa-helper.dev"
    cert_path = config_path / Path("cert.pem")
    key_path = config_path / Path("key.pem")

    env = {
        **os.environ,
        "BASE_DOMAIN": base_domain,
        "TRAEFIK_PROVIDERS_HTTP_TLS_CERT": cert_path,
        "TRAEFIK_PROVIDERS_HTTP_TLS_KEY": key_path,
        "TRAEFIK_PROVIDERS_FILE_FILENAME": Path("sidecar/dynamic_conf.yaml"),
    }
    cmd = "./traefik --configFile=sidecar/traefik.yaml"
    return Command(cmd=cmd, env=env)


@cli.command
@click.option(
    "--config_path",
    type=click_pathlib.Path(exists=True),
    default=Path("local_dev/config"),
    show_default=True,
)
@click.option("--root_path", type=click_pathlib.Path(), default=None)
@click.option("--identity", required=True, type=int)
def start_helper_sidecar(
    config_path: Path,
    root_path: Optional[Path],
    identity: int,
):
    sidecar_command = start_helper_sidecar_command(
        config_path,
        identity,
        root_path,
    )
    traefik_command = start_traefik_command(
        config_path,
        identity,
        root_path,
    )
    start_commands_parallel([sidecar_command, traefik_command])


@cli.command
@click.option(
    "--config_path",
    type=click_pathlib.Path(exists=True),
    default=Path("local_dev/config"),
    show_default=True,
)
@click.option("--root_path", type=click_pathlib.Path(), default=None)
def start_local_dev(
    config_path: Path,
    root_path: Optional[Path],
):
    npm_install_command = Command(
        cmd="npm --prefix server install",
    )
    npm_install_command.run_blocking_no_output_capture()
    npm_run_dev_command = Command(
        cmd="npm --prefix server run dev",
    )

    network_config = Path(config_path) / Path("network.toml")
    helpers = load_helpers_from_network_config(network_config)
    sidecar_commands = [
        start_helper_sidecar_command(
            config_path,
            helper.role,
            root_path,
        )
        for helper in helpers.values()
    ]
    commands = [npm_run_dev_command] + sidecar_commands
    start_commands_parallel(commands)


if __name__ == "__main__":
    cli()
