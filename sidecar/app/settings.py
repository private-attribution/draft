from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

import loguru
from loguru import logger
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
    _logger: Any  # cannot use loguru.Logger here because pydantic tries to import it

    def model_post_init(self, __context) -> None:
        self._helpers = load_helpers_from_network_config(self.network_config_path)
        self._logger = logger
        self._logger.remove()
        max_role_str_len = max(len(role.name) for role in Role)
        role_str = f"{self.role.name.replace('_', ' ').title():>{max_role_str_len}}"

        logger_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<blue>{extra[role]}</blue> - <level>{message}</level>"
        )
        self._logger.configure(extra={"role": role_str})
        self._logger.add(
            sys.stderr,
            level="INFO",
            format=logger_format,
        )

    @property
    def logger(self) -> loguru.Logger:
        return self._logger

    @property
    def helper(self) -> Helper:
        return self._helpers[self.role]

    @property
    def helpers(self) -> dict[Role, Helper]:
        return self._helpers

    @property
    def status_dir_path(self) -> Path:
        return self.root_path / Path("status")

    @property
    def log_dir_path(self) -> Path:
        return self.root_path / Path("logs")


@lru_cache
def get_settings():
    settings = Settings()
    settings.status_dir_path.mkdir(exist_ok=True)
    settings.log_dir_path.mkdir(exist_ok=True)
    return settings
