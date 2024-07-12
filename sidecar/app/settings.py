from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic.functional_validators import BeforeValidator
from pydantic_settings import BaseSettings

from .helpers import Helper, Role, load_helpers_from_network_config


def gen_path(v: Any) -> Path:
    return Path(v)


class Settings(BaseSettings):
    root_path: Annotated[Path, BeforeValidator(gen_path)]
    config_path: Annotated[Path, BeforeValidator(gen_path)]
    network_config_path: Annotated[Path, BeforeValidator(gen_path)]
    role: Role
    helper_port: int
    _helpers: dict[Role, Helper]

    def model_post_init(self, __context) -> None:
        self._helpers = load_helpers_from_network_config(self.network_config_path)

    @property
    def helper(self):
        return self._helpers[self.role]

    @property
    def helpers(self):
        return self._helpers

    @property
    def status_dir_path(self):
        return self.root_path / Path("status")

    @property
    def log_dir_path(self):
        return self.root_path / Path("logs")


@lru_cache
def get_settings():
    settings = Settings()
    settings.status_dir_path.mkdir(exist_ok=True)
    settings.log_dir_path.mkdir(exist_ok=True)
    return settings
