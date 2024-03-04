import os
from pathlib import Path
from typing import Optional

import click
import click_pathlib

from ..app.command import Command, start_commands_parallel
from ..app.helpers import Role


@click.group()
def cli():
    pass


def start_helper_sidecar_command(
    config_path: Path,
    identity: int,
    helper_port: int,
    sidecar_port: int,
    root_path: Optional[Path] = None,
):
    role = Role(int(identity))
    network_config = config_path / Path("network.toml")
    root_path = root_path or Path(f"tmp/sidecar/{role.value}")
    root_path.mkdir(parents=True, exist_ok=True)
    if role == Role.COORDINATOR:
        private_key_pem_path = config_path / Path("coordinator.key")
    else:
        private_key_pem_path = config_path / Path(f"h{role.value}.key")
    cmd = "uvicorn sidecar.app.main:app"
    env = {
        **os.environ,
        "ROLE": str(role.value),
        "ROOT_PATH": root_path,
        "CONFIG_PATH": config_path,
        "NETWORK_CONFIG_PATH": network_config,
        "PRIVATE_KEY_PEM_PATH": private_key_pem_path,
        "HELPER_PORT": str(helper_port),
        "UVICORN_PORT": str(sidecar_port),
        "UVICORN_HOST": "0.0.0.0",
    }
    return Command(cmd=cmd, env=env)


def build_domains(
    identity: int,
    root_domain: str,
) -> tuple[str, str]:
    role = Role(int(identity))
    if role == Role.COORDINATOR:
        sidecar_domain = f"sidecar-coordinator.{root_domain}"
        helper_domain = f"helper-coordinator.{root_domain}"
    else:
        sidecar_domain = f"sidecar{role.value}.{root_domain}"
        helper_domain = f"helper{role.value}.{root_domain}"
    return sidecar_domain, helper_domain


# pylint: disable=too-many-arguments
def start_traefik_command(
    config_path: Path,
    helper_port: int,
    sidecar_port: int,
    root_domain: str,
    helper_domain: str,
    sidecar_domain: str,
):
    helper_domain = helper_domain or f"helper.{root_domain}"
    sidecar_domain = sidecar_domain or f"sidecar.{root_domain}"
    env = {
        **os.environ,
        "HELPER_DOMAIN": helper_domain,
        "SIDECAR_DOMAIN": sidecar_domain,
        "HELPER_PORT": str(helper_port),
        "SIDECAR_PORT": str(sidecar_port),
        "CERT_DIR": config_path,
    }
    cmd = "sudo -E ./traefik --configFile=sidecar/traefik/traefik.yaml"
    return Command(cmd=cmd, env=env)


def start_traefik_local_command(
    config_path: Path,
    helper_ports: tuple[int, ...],
    sidecar_ports: tuple[int, ...],
    server_port: int,
    root_domain: str,
):
    env = {
        **os.environ,
        "CERT_DIR": config_path,
        "SERVER_DOMAIN": root_domain,
        "SERVER_PORT": str(server_port),
    }
    for identity, (h_port, s_port) in enumerate(zip(helper_ports, sidecar_ports)):
        sidecar_domain, helper_domain = build_domains(identity, root_domain)
        env[f"SIDECAR_{identity}_DOMAIN"] = sidecar_domain
        env[f"SIDECAR_{identity}_PORT"] = str(s_port)
        env[f"HELPER_{identity}_DOMAIN"] = helper_domain
        env[f"HELPER_{identity}_PORT"] = str(h_port)

    cmd = "traefik --configFile=sidecar/traefik/traefik-local.yaml"
    return Command(cmd=cmd, env=env)


# pylint: disable=too-many-arguments
@cli.command
@click.option(
    "--config_path",
    type=click_pathlib.Path(exists=True),
    default=Path("local_dev/config"),
    show_default=True,
)
@click.option("--root_path", type=click_pathlib.Path(), default=None)
@click.option("--root_domain", type=str, default="ipa-helper.dev")
@click.option("--helper_domain", type=str, default="")
@click.option("--sidecar_domain", type=str, default="")
@click.option("--helper_port", type=int, default=7430)
@click.option("--sidecar_port", type=int, default=17430)
@click.option("--identity", required=True, type=int)
def start_helper_sidecar(
    config_path: Path,
    root_path: Optional[Path],
    root_domain: str,
    helper_domain: str,
    sidecar_domain: str,
    helper_port: int,
    sidecar_port: int,
    identity: int,
):
    sidecar_command = start_helper_sidecar_command(
        config_path=config_path,
        identity=identity,
        helper_port=helper_port,
        sidecar_port=sidecar_port,
        root_path=root_path,
    )
    traefik_command = start_traefik_command(
        config_path=config_path,
        helper_port=helper_port,
        sidecar_port=sidecar_port,
        root_domain=root_domain,
        helper_domain=helper_domain,
        sidecar_domain=sidecar_domain,
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
@click.option("--helper_start_port", type=int, default=7430)
@click.option("--sidecar_start_port", type=int, default=17430)
def start_local_dev(
    config_path: Path,
    root_path: Optional[Path],
    helper_start_port: int,
    sidecar_start_port: int,
):
    root_domain: str = "draft.test"
    server_port: int = 7530
    npm_install_command = Command(
        cmd="npm --prefix server install",
    )
    npm_install_command.run_blocking_no_output_capture()
    npm_run_dev_command = Command(
        cmd=f"npm --prefix server run dev -- --port {server_port}",
    )

    helper_ports = {role: helper_start_port + int(role) for role in Role}
    sidecar_ports = {role: sidecar_start_port + int(role) for role in Role}

    sidecar_commands = [
        start_helper_sidecar_command(
            config_path=config_path,
            identity=role,
            helper_port=helper_ports[role],
            sidecar_port=sidecar_ports[role],
            root_path=root_path,
        )
        for role in Role
    ]
    traefik_command = start_traefik_local_command(
        config_path=config_path,
        helper_ports=tuple(helper_ports.values()),
        sidecar_ports=tuple(sidecar_ports.values()),
        server_port=server_port,
        root_domain=root_domain,
    )
    commands = sidecar_commands + [npm_run_dev_command, traefik_command]
    start_commands_parallel(commands)


if __name__ == "__main__":
    cli()
