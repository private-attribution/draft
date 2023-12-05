import time
import asyncio
import psutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from app.processes import processes
from app.logging import (
    gen_process_complete_semaphore_path,
    gen_log_file_path,
)

router = APIRouter(
    prefix="/ws",
    tags=[
        "websockets",
    ],
)


@router.websocket("/status/{process_id}")
async def status_websocket(websocket: WebSocket, process_id: str):
    complete_semaphore = gen_process_complete_semaphore_path(process_id)
    process, _ = processes.get(process_id, (None, None))
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


@router.websocket("/logs/{process_id}")
async def logs_websocket(websocket: WebSocket, process_id: str):
    log_file_path = gen_log_file_path(process_id)
    complete_semaphore = gen_process_complete_semaphore_path(process_id)
    process, _ = processes.get(process_id, (None, None))

    await websocket.accept()

    while process is not None and not log_file_path.exists():
        logger.warning(f"{process_id=} started. log file does not yet exist. waiting.")
        asyncio.sleep(1)

    if process is None and not log_file_path.exists():
        logger.warning(f"{process_id=} does not exist.")
        await websocket.close()
    else:
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


@router.websocket("/stats/{process_id}")
async def stats_websocket(websocket: WebSocket, process_id: str):
    process, start_time = processes.get(process_id, (None, None))
    complete_semaphore = gen_process_complete_semaphore_path(process_id)

    await websocket.accept()

    if process is None or complete_semaphore.exists():
        logger.warning(f"{process_id=} is not running.")
        await websocket.close()

    else:
        pid = process.pid
        process_psutil = psutil.Process(pid)
        try:
            while process.poll() is None:
                try:
                    run_time = time.time() - start_time
                    logger.info(f"{run_time=}")
                    cpu_percent = process_psutil.cpu_percent()
                    logger.info(f"{cpu_percent=}")
                    memory_info = process_psutil.memory_info()
                    logger.info(f"{memory_info=}")
                    await websocket.send_json(
                        {
                            "run_time": run_time,
                            "cpu_percent": cpu_percent,
                            "memory_info": memory_info,
                            "timestamp": time.time(),
                        }
                    )
                    await asyncio.sleep(1)
                except psutil.NoSuchProcess:
                    break
            await websocket.close()

        except WebSocketDisconnect:
            pass
