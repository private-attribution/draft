from pathlib import Path
from typing import Annotated, Any

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from pydantic.functional_validators import BeforeValidator
from pydantic_settings import BaseSettings

from .helpers import Helper, Role, load_helpers_from_network_config


def gen_path(v: Any) -> Path:
    return Path(v)


# pyre-ignore: https://pyre-check.org/docs/errors/#dataclass-like-classes
class Settings(BaseSettings):
    root_path: Annotated[Path, BeforeValidator(gen_path)]
    config_path: Annotated[Path, BeforeValidator(gen_path)]
    network_config_path: Annotated[Path, BeforeValidator(gen_path)]
    private_key_pem_path: Annotated[Path, BeforeValidator(gen_path)]
    role: Role
    _helpers: dict[Role, Helper]
    _private_key: EllipticCurvePrivateKey

    def model_post_init(self, __context) -> None:
        self._helpers = load_helpers_from_network_config(self.network_config_path)
        with self.private_key_pem_path.open("rb") as f:
            _private_key = load_pem_private_key(f.read(), None)
        assert isinstance(_private_key, EllipticCurvePrivateKey)
        self._private_key = _private_key

    @property
    def helper(self):
        return self._helpers[self.role]

    @property
    def helpers(self):
        return self._helpers

    @property
    def private_key(self):
        return self.private_key


settings = Settings()
