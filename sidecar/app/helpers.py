from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import tomllib
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.x509 import load_pem_x509_certificate


class Role(IntEnum):
    COORDINATOR = 0
    HELPER_1 = 1
    HELPER_2 = 2
    HELPER_3 = 3


@dataclass
class Helper:
    role: Role
    helper_url: ParseResult
    sidecar_url: ParseResult
    public_key: EllipticCurvePublicKey


def load_helpers_from_network_config(network_config_path: Path) -> dict[Role, Helper]:
    with network_config_path.open("rb") as f:
        network_data = tomllib.load(f)
        helper_configs = network_data["peers"]
        helper_roles = list(r for r in Role if r != Role.COORDINATOR)
        helpers = {}
        for helper_config, role in zip(helper_configs, helper_roles):
            helper_url = urlparse(f"http://{helper_config['url']}")
            sidecar_url = urlparse(f"http://{helper_config['sidecar_url']}")
            public_key_pem_data = helper_config.get("certificate")
            cert = load_pem_x509_certificate(public_key_pem_data.encode("utf8"))
            public_key = cert.public_key()
            assert isinstance(public_key, EllipticCurvePublicKey)
            helpers[role] = Helper(
                role=role,
                helper_url=helper_url,
                sidecar_url=sidecar_url,
                public_key=public_key,
            )

        helper_url = urlparse(f"http://{network_data['coordinator']['url']}")
        sidecar_url = urlparse(f"http://{network_data['coordinator']['sidecar_url']}")
        public_key_pem_data = network_data["coordinator"].get("certificate")
        cert = load_pem_x509_certificate(public_key_pem_data.encode("utf8"))
        public_key = cert.public_key()
        assert isinstance(public_key, EllipticCurvePublicKey)

        helpers[Role.COORDINATOR] = Helper(
            role=Role.COORDINATOR,
            helper_url=helper_url,
            sidecar_url=sidecar_url,
            public_key=public_key,
        )
        return helpers
