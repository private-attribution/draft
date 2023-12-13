import subprocess
import shlex
import threading
import time
from typing import Annotated
from loguru import logger
from fastapi import APIRouter, Form
from ..processes import processes
from ..logging import log_process_stdout
from ..settings import settings


router = APIRouter(
    prefix="/start",
    tags=[
        "start",
    ],
)


def start_process(cmd, process_id: str):
    if processes.get(process_id):
        raise Exception(f"{process_id} already exists")

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    start_time = time.time()

    # Store process information
    processes[process_id] = (process, start_time)
    logger.info(f"process started: {process_id=}")

    # Start a new thread to tail logs to the file
    log_thread = threading.Thread(
        target=log_process_stdout,
        args=(process_id,),
        daemon=True,
    )
    log_thread.start()


@router.post("/demo-logger/{process_id}")
def demo_logger(
    process_id: str,
    num_lines: Annotated[int, Form()],
    total_runtime: Annotated[int, Form()],
):
    cmd = f"""
    .venv/bin/python logger --num-lines {num_lines} --total-runtime {total_runtime}
    """
    start_process(shlex.split(cmd), process_id)
    return {"message": "Process started successfully", "process_id": process_id}
