import asyncio
import time
from contextlib import asynccontextmanager

import psutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets import ConnectionClosedError, ConnectionClosedOK

from ..logger import logger
from ..queries import Query, Status

router = APIRouter(
    prefix="/ws",
    tags=[
        "websockets",
    ],
)


@asynccontextmanager
async def use_websocket(websocket):
    await websocket.accept()
    try:
        yield websocket
    except (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosedError):
        pass
    finally:
        await websocket.close()


@router.websocket("/status/{query_id}")
async def status_websocket(websocket: WebSocket, query_id: str):
    query = Query.get_from_query_id(query_id)
    async with use_websocket(websocket) as websocket:
        if query is None:
            logger.warning(f"{query_id=} Status: {Status.NOT_FOUND.name}")
            await websocket.send_json({"status": Status.NOT_FOUND.name})
        else:
            while not query.done:
                logger.debug(f"{query_id=} Status: {query.status.name}")
                await websocket.send_json({"status": query.status.name})
                await asyncio.sleep(1)

            logger.debug(f"{query_id=} Status: {query.status.name}")
            await websocket.send_json({"status": query.status.name})


@router.websocket("/logs/{query_id}")
async def logs_websocket(websocket: WebSocket, query_id: str):
    query = Query.get_from_query_id(query_id)

    async with use_websocket(websocket) as websocket:
        if query is None:
            logger.warning(f"{query_id=} does not exist.")
            return

        with open(query.log_file_path, "r", encoding="utf8") as log_file:
            if query.done:
                logger.info(f"{query_id=} complete. sending all logs.")
                for line in log_file:
                    await websocket.send_text(line)
            else:
                logger.info(f"{query_id=} running. tailing log file.")
                while not query.done:
                    line = log_file.readline()
                    if not line:
                        await asyncio.sleep(0.1)
                    else:
                        await websocket.send_text(line)


@router.websocket("/stats/{query_id}")
async def stats_websocket(websocket: WebSocket, query_id: str):
    query = Query.get_from_query_id(query_id)
    async with use_websocket(websocket) as websocket:
        if query is None or query.done or query.current_process is None:
            logger.warning(f"{query_id=} is not running.")
            return

        process_psutil = psutil.Process(query.current_process.pid)
        while query.running:
            try:
                run_time = query.run_time
                cpu_percent = process_psutil.cpu_percent()
                memory_info = process_psutil.memory_info()
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
                return
