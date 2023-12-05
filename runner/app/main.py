import subprocess
import threading
import time
from haikunator import Haikunator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.words import nouns, adjectives
from app.processes import processes
from app.logging import log_process_stdout
from app.routes import websockets

app = FastAPI()
app.include_router(websockets.router)

haikunator = Haikunator(
    nouns=nouns,
    adjectives=adjectives,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/start")
async def start():
    cmd = [
        "/Users/eriktaubeneck/workspace/remote-runner/.venv/bin/python",
        "/Users/eriktaubeneck/workspace/remote-runner/logger",
    ]
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

    return {"message": "Process started successfully", "process_id": process_id}
