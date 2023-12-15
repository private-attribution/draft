import asyncio
import psutil
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from ..processes import queries, Status, gen_process_complete_semaphore_path
from ..logging import gen_log_file_path

router = APIRouter(
    prefix="/ws",
    tags=[
        "websockets",
    ],
)


@router.websocket("/status/{process_id}")
async def status_websocket(websocket: WebSocket, process_id: str):
    complete_semaphore = gen_process_complete_semaphore_path(process_id)
    query = queries.get(process_id)
    await websocket.accept()
    try:
        if complete_semaphore.exists():
            logger.info(f"{process_id=} Status: complete")
            await websocket.send_json({"status": Status.COMPLETE.name})
        elif query is not None:
            while not complete_semaphore.exists():
                await asyncio.sleep(1)
                logger.info(f"{process_id=} Status: {query.status}")
                await websocket.send_json({"status": query.status.name})
            await websocket.send_json({"status": Status.COMPLETE.name})
        else:
            logger.warning(f"{process_id=} Status: {Status.NOT_FOUND.name}")
            await websocket.send_json({"status": Status.NOT_FOUND.name})
        await websocket.close()
    except WebSocketDisconnect:
        pass


@router.websocket("/logs/{process_id}")
async def logs_websocket(websocket: WebSocket, process_id: str):
    log_file_path = gen_log_file_path(process_id)
    complete_semaphore = gen_process_complete_semaphore_path(process_id)
    query = queries.get(process_id)

    await websocket.accept()

    while query is not None and not log_file_path.exists():
        logger.warning(f"{process_id=} started. log file does not yet exist. waiting.")
        asyncio.sleep(1)

    if query is None and not log_file_path.exists():
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
    query = queries.get(process_id)
    complete_semaphore = gen_process_complete_semaphore_path(process_id)

    await websocket.accept()

    if query is None or complete_semaphore.exists():
        logger.warning(f"{process_id=} is not running.")
        await websocket.close()

    else:
        pid = query.current_process.pid
        process_psutil = psutil.Process(pid)
        try:
            while query.current_process.poll() is None:
                try:
                    run_time = query.run_time
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
