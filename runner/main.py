import subprocess
import threading
import asyncio
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests only from http://localhost:3001
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:3001"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Dictionary to store process information
processes = {}


def tail_logs_to_file(process_id, log_file_path):
    process_info = processes.get(process_id)

    if process_info is None:
        return

    process = process_info["process"]

    with open(log_file_path, "a") as log_file:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            log_file.write(line)


async def tail_logs_from_file(websocket, log_file_path):
    try:
        with open(log_file_path, "r") as log_file:
            while True:
                line = log_file.readline()
                if not line:
                    await asyncio.sleep(0.1)
                else:
                    await websocket.send_text(line)
    except WebSocketDisconnect:
        pass


def log_file_path(process_id):
    return f"tmp/logs/log_{process_id}.txt"


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/start")
async def start():
    cmd = [
        "/Users/eriktaubeneck/workspace/remote-runner/.venv/bin/python",
        "/Users/eriktaubeneck/workspace/remote-runner/logger",
    ]
    process_id = uuid4().hex

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    # Store process information
    processes[process_id] = {
        "process": process,
        "log_file_path": log_file_path(process_id),
    }

    # Start a new thread to tail logs to the file
    log_thread = threading.Thread(
        target=tail_logs_to_file,
        args=(process_id, log_file_path(process_id)),
        daemon=True,
    )
    log_thread.start()

    return {"message": "Process started successfully", "process_id": process_id}


@app.websocket("/ws/{process_id}")
async def websocket_endpoint(websocket: WebSocket, process_id: str):
    await websocket.accept()

    # Start a new thread to tail logs from the file
    log_thread = threading.Thread(
        target=asyncio.run,
        args=(tail_logs_from_file(websocket, log_file_path(process_id)),),
        daemon=True,
    )
    log_thread.start()

    try:
        while True:
            await asyncio.sleep(0.1)  # Sleep briefly to avoid high CPU usage

    except WebSocketDisconnect:
        # Cleanup resources when the WebSocket disconnects
        log_thread.join()
