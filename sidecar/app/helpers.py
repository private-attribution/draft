from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import tomllib


class Role(IntEnum):
    COORDINATOR = 0
    HELPER_1 = 1
    HELPER_2 = 2
    HELPER_3 = 3


@dataclass
class Helper:
    role: Role
    hostname: str
    sidecar_port: int
    helper_port: int

    @property
    def sidecar_url(self) -> ParseResult:
        return urlparse(f"http://{self.hostname}:{self.sidecar_port}")

    @property
    def helper_url(self) -> ParseResult:
        return urlparse(f"http://{self.hostname}:{self.helper_port}")


def load_helpers_from_network_config(network_config_path: Path) -> dict[Role, Helper]:
    with network_config_path.open("rb") as f:
        network_data = tomllib.load(f)
        helper_configs = network_data["peers"]
        helper_roles = list(r for r in Role if r != Role.COORDINATOR)
        helpers = {}
        for helper_config, role in zip(helper_configs, helper_roles):
            url = urlparse(f"http://{helper_config['url']}")
            hostname = str(url.hostname)
            helper_port = int(url.port or 0)
            sidecar_port = int(helper_config.get("sidecar_port", 0))
            if not hostname or not helper_port or not sidecar_port:
                raise Exception(f"{network_data=} missing data.")
            helpers[role] = Helper(
                role=role,
                hostname=hostname,
                helper_port=helper_port,
                sidecar_port=sidecar_port,
            )

        url = urlparse(f"http://{network_data['coordinator']['url']}")
        hostname = str(url.hostname)
        helper_port = int(url.port or 0)
        sidecar_port = int(network_data["coordinator"].get("sidecar_port", 0))
        if not hostname or not helper_port or not sidecar_port:
            raise Exception(f"{network_data=} missing data.")

        helpers[Role.COORDINATOR] = Helper(
            role=Role.COORDINATOR,
            hostname=hostname,
            helper_port=helper_port,
            sidecar_port=sidecar_port,
        )
        return helpers
