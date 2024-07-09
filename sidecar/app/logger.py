import sys

from loguru import logger

from .helpers import Role
from .settings import get_settings


def get_logger():
    settings = get_settings()
    logger.remove()
    max_role_str_len = max(len(role.name) for role in Role)
    role_str = f"{settings.role.name.replace('_', ' ').title():>{max_role_str_len}}"

    logger_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<blue>{extra[role]}</blue> - <level>{message}</level>"
    )
    logger.configure(extra={"role": role_str})
    logger.add(
        sys.stderr,
        level="INFO",
        format=logger_format,
    )
    return logger
