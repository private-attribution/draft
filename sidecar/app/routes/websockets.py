import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from websockets import ConnectionClosedError, ConnectionClosedOK

from ..query.base import Query
from .http_helpers import get_query_from_query_id

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
    else:
        await websocket.close()


@router.websocket("/status/{query_id}")
async def status_websocket(
    websocket: WebSocket,
    query_id: str,
):
    query_manager = websocket.app.state.QUERY_MANAGER
    query = query_manager.get_from_query_id(Query, query_id)
    if query is None:
        raise HTTPException(status_code=404, detail="Query not found")

    async with use_websocket(websocket) as websocket:
        while query.running:
            await websocket.send_json(query.status_event_json)
            await asyncio.sleep(1)

        await websocket.send_json(query.status_event_json)


@router.websocket("/logs/{query_id}")
async def logs_websocket(
    websocket: WebSocket,
    query_id: str,
):
    query = get_query_from_query_id(websocket.app.state.QUERY_MANAGER, Query, query_id)

    async with use_websocket(websocket) as websocket:
        with open(query.log_file_path, "r", encoding="utf8") as log_file:
            if query.finished:
                query.logger.info(f"{query_id=} complete. sending all logs.")
                for line in log_file:
                    await websocket.send_text(line)
            else:
                query.logger.info(f"{query_id=} running. tailing log file.")
                while query.running:
                    line = log_file.readline()
                    if not line:
                        await asyncio.sleep(0.1)
                    else:
                        await websocket.send_text(line)
                for line in log_file:
                    await websocket.send_text(line)


@router.websocket("/stats/{query_id}")
async def stats_websocket(
    websocket: WebSocket,
    query_id: str,
):
    query = get_query_from_query_id(websocket.app.state.QUERY_MANAGER, Query, query_id)

    async with use_websocket(websocket) as websocket:
        if query.finished:
            query.logger.warning(f"{query_id=} is finished.")
            return
        while query.running:
            await websocket.send_json(
                {
                    "cpu_percent": query.cpu_usage_percent,
                    "memory_rss_usage": query.memory_rss_usage,
                    "timestamp": time.time(),
                }
            )
            await asyncio.sleep(1)
