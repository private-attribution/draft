from pathlib import Path
from loguru import logger
from .settings import settings

log_path = settings.root_path / Path("logs")
log_path.mkdir(exist_ok=True, parents=True)


def gen_log_file_path(query_id):
    return log_path / Path(f"{query_id}.log")


def log_process_stdout(query_id, process):
    logger.debug(query_id)
    logger.debug(process)

    if process is None:
        return

    process_logger = logger.bind(task="process_tail")
    logger.add(
        gen_log_file_path(query_id),
        format="{message}",
        filter=lambda record: record["extra"].get("task") == "process_tail",
        enqueue=True,
    )

    while True:
        line = process.stdout.readline()
        if not line:
            break
        process_logger.info(line.rstrip("\n"))
