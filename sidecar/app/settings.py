from enum import Enum
from pathlib import Path
from typing import Annotated, Any

from pydantic.functional_validators import BeforeValidator
from pydantic_settings import BaseSettings


class Role(int, Enum):
    COORDINATOR = 0
    HELPER_1 = 1
    HELPER_2 = 2
    HELPER_3 = 3


def gen_path(v: Any) -> Path:
    return Path(v)


# pyre-ignore: https://pyre-check.org/docs/errors/#dataclass-like-classes
class Settings(BaseSettings):
    root_path: Annotated[Path, BeforeValidator(gen_path)]
    config_path: Annotated[Path, BeforeValidator(gen_path)]
    role: Role


settings = Settings()
print(settings)
