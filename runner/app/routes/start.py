import subprocess
import threading
import time
from typing import Annotated
from loguru import logger
from fastapi import APIRouter, Form
from haikunator import Haikunator
from ..processes import processes
from ..words import nouns, adjectives
from ..logging import log_process_stdout


router = APIRouter(
    prefix="/start",
    tags=[
        "start",
    ],
)

haikunator = Haikunator(
    nouns=nouns,
    adjectives=adjectives,
)


def start_process(cmd):
    process_id = str(haikunator.haikunate(token_length=4))

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
    return process_id


@router.post("/demo-logger")
def demo_logger(
    num_lines: Annotated[int, Form()],
    total_runtime: Annotated[int, Form()],
):
    logger.info("here")
    logger.info(f"{num_lines=}")
    logger.info(f"{total_runtime=}")
    cmd = [
        ".venv/bin/python",
        "logger",
        "--num-lines",
        str(num_lines),
        "--total-runtime",
        str(total_runtime),
    ]
    process_id = start_process(cmd)
    return {"message": "Process started successfully", "process_id": process_id}
