from pathlib import Path
from loguru import logger
from .processes import processes
from .settings import settings

log_path = settings.root_path / Path("logs")
log_path.mkdir(exist_ok=True, parents=True)
complete_semaphore_path = settings.root_path / Path("complete_semaphore")
complete_semaphore_path.mkdir(exist_ok=True, parents=True)


def gen_log_file_path(process_id):
    return log_path / Path(f"{process_id}.log")


def gen_process_complete_semaphore_path(process_id):
    return complete_semaphore_path / Path(f"{process_id}")


def log_process_stdout(process_id):
    logger.debug(process_id)
    process, _ = processes.get(process_id, (None, None))
    logger.debug(process)

    if process is None:
        return

    process_logger = logger.bind(task="process_tail")
    logger.add(
        gen_log_file_path(process_id),
        format="{message}",
        filter=lambda record: record["extra"].get("task") == "process_tail",
    )

    while True:
        line = process.stdout.readline()
        if not line:
            break
        process_logger.info(line.rstrip("\n"))
    complete_semaphore = gen_process_complete_semaphore_path(process_id)
    complete_semaphore.touch()
    del processes[process_id]
