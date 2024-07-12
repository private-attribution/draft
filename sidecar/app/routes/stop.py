from fastapi import APIRouter

from ..logger import logger
from ..query.base import Query
from ..query.status import Status

router = APIRouter(
    prefix="/stop",
    tags=[
        "stop",
    ],
)


@router.post("/finish/{query_id}")
def finish(
    query_id: str,
):
    query = Query.get_from_query_id(query_id)
    if query is None:
        return {"message": "Query not found", "query_id": query_id}
    logger.info(f"{query=}")
    if query.status < Status.COMPLETE:
        logger.info("calling query finish")
        query.finish()
        return {"message": "Query stopped successfully", "query_id": query_id}
    return {"message": "Query already complete", "query_id": query_id}


@router.post("/kill/{query_id}")
def kill(
    query_id: str,
):
    logger.info(f"kill called for {query_id=}")
    query = Query.get_from_query_id(query_id)
    if query is None:
        return {"message": "Query not found", "query_id": query_id}
    if query.status < Status.COMPLETE:
        query.kill()
        return {"message": "Query killed", "query_id": query_id}
    return {"message": "Query already complete", "query_id": query_id}
