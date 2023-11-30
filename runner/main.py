import subprocess
import threading
import asyncio
from pathlib import Path
from haikunator import Haikunator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

app = FastAPI()
haikunator = Haikunator()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Dictionary to store process information
processes = {}

log_path = Path("tmp/logs")
log_path.mkdir(exist_ok=True)
complete_semaphore_path = Path("tmp/complete_semaphore")
complete_semaphore_path.mkdir(exist_ok=True)


def gen_log_file_path(process_id):
    return log_path / Path(f"{process_id}.log")


def gen_process_complete_semaphore_path(process_id):
    return complete_semaphore_path / Path(f"{process_id}")


def log_process_stodout(process_id):
    logger.debug(process_id)
    process = processes.get(process_id)
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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/start")
async def start():
    cmd = [
        "/Users/eriktaubeneck/workspace/remote-runner/.venv/bin/python",
        "/Users/eriktaubeneck/workspace/remote-runner/logger",
    ]
    process_id = str(haikunator.haikunate(token_length=0))

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    # Store process information
    processes[process_id] = process
    logger.info(f"process started: {process_id=}")

    # Start a new thread to tail logs to the file
    log_thread = threading.Thread(
        target=log_process_stodout,
        args=(process_id,),
        daemon=True,
    )
    log_thread.start()

    return {"message": "Process started successfully", "process_id": process_id}


@app.websocket("/ws/status/{process_id}")
async def status_websocket(websocket: WebSocket, process_id: str):
    complete_semaphore = gen_process_complete_semaphore_path(process_id)
    process = processes.get(process_id)
    await websocket.accept()
    try:
        if complete_semaphore.exists():
            logger.info(f"{process_id=} Status: complete")
            await websocket.send_json({"status": "complete"})
        elif process is not None:
            while not complete_semaphore.exists():
                await asyncio.sleep(1)
                logger.info(f"{process_id=} Status: in-progress")
                await websocket.send_json({"status": "in-progress"})
            await websocket.send_json({"status": "complete"})
        else:
            logger.warning(f"{process_id=} Status: not found")
            await websocket.send_json({"status": "not-found"})
        await websocket.close()
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/logs/{process_id}")
async def logs_websocket(websocket: WebSocket, process_id: str):
    log_file_path = gen_log_file_path(process_id)
    complete_semaphore = gen_process_complete_semaphore_path(process_id)
    process = processes.get(process_id)

    while process is not None and not log_file_path.exists():
        logger.warning(f"{process_id=} started. log file does not yet exist. waiting.")
        asyncio.sleep(1)

    if process is None and not log_file_path.exists():
        logger.warning(f"{process_id=} does not exist.")
        return

    await websocket.accept()
    try:
        with open(log_file_path, "r") as log_file:
            if complete_semaphore.exists():
                logger.info(f"{process_id=} complete. sending all logs.")
                for line in log_file:
                    await websocket.send_text(line)
            else:
                logger.info(f"{process_id=} running. tailing log file.")
                while not complete_semaphore.exists():
                    line = log_file.readline()
                    if not line:
                        await asyncio.sleep(0.1)
                    else:
                        await websocket.send_text(line)
        await websocket.close()
    except WebSocketDisconnect:
        pass
