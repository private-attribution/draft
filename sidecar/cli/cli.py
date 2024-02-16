import os
from pathlib import Path
from typing import Optional

import click
import click_pathlib
import yaml

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


def create_dynamic_config(
    base_domain: str, config_path: Path, sidecar_port=int, ipa_port=int
):
    data = {
        "tls": {
            "options": {
                "default": {
                    "minVersion": "VersionTLS12",
                    "cipherSuites": ["TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"],
                }
            }
        },
        "http": {
            "routers": {
                "service1": {
                    "rule": f"Host(`{base_domain}`)",
                    "service": "service1",
                    "entryPoints": ["web-secure"],
                    "tls": {"options": "default"},
                },
                "service2": {
                    "rule": f"Host(`ipa.{base_domain}`)",
                    "service": "service2",
                    "entryPoints": ["web-secure"],
                    "tls": {"options": "default"},
                },
            },
            "services": {
                "service1": {
                    "loadBalancer": {
                        "servers": [{"url": f"http://localhost:{sidecar_port}"}]
                    }
                },
                "service2": {
                    "loadBalancer": {
                        "servers": [{"url": f"http://localhost:{ipa_port}"}]
                    }
                },
            },
        },
    }
    with config_path.open(mode="w") as f:
        yaml.dump(data, f)


def create_tls_config(cert_path: Path, key_path: Path, config_path: Path):
    data = {
        "tls": {
            "stores": {
                "default": {
                    "defaultCertificate": {
                        "certFile": str(cert_path.absolute()),
                        "keyFile": str(key_path.absolute()),
                    }
                }
            }
        }
    }
    with config_path.open(mode="w") as f:
        yaml.dump(data, f)


def start_traefik_command(
    config_path: Path,
    identity: int,
    root_domain: str,
    root_path: Optional[Path] = None,
):
    role = Role(int(identity))
    root_path = root_path or Path(f"tmp/sidecar/{role.value}")
    if role == Role.COORDINATOR:
        base_domain = f"coordinator.{root_domain}"
    else:
        base_domain = f"helper{role.value}.{root_domain}"
    network_config = config_path / Path("network.toml")
    helpers = load_helpers_from_network_config(network_config)
    helper = helpers[role]
    cert_path = config_path / Path("cert.pem")
    key_path = config_path / Path("key.pem")
    tls_config_path = Path("sidecar/traefik/dynamic/tls_conf.yaml")
    create_tls_config(
        cert_path=cert_path,
        key_path=key_path,
        config_path=tls_config_path,
    )
    dynamic_config_path = Path("sidecar/traefik/dynamic/dyanmic_conf.yaml")
    create_dynamic_config(
        base_domain=base_domain,
        config_path=dynamic_config_path,
        sidecar_port=helper.helper_port,
        ipa_port=helper.helper_port + 1,
    )

    env = {
        **os.environ,
        "BASE_DOMAIN": base_domain,
    }
    cmd = "sudo ./traefik --configFile=sidecar/traefik/traefik.yaml"
    return Command(cmd=cmd, env=env)


@cli.command
@click.option(
    "--config_path",
    type=click_pathlib.Path(exists=True),
    default=Path("local_dev/config"),
    show_default=True,
)
@click.option("--root_path", type=click_pathlib.Path(), default=None)
@click.option("--root_domain", type=str, default="ipa-helper.dev")
@click.option("--identity", required=True, type=int)
def start_helper_sidecar(
    config_path: Path,
    root_path: Optional[Path],
    root_domain: str,
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
        root_domain,
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
