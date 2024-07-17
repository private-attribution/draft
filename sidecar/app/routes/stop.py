from fastapi import APIRouter, Request

from ..query.base import Query
from ..query.status import Status
from .http_helpers import get_query_from_query_id

router = APIRouter(
    prefix="/stop",
    tags=[
        "stop",
    ],
)


@router.post("/finish/{query_id}")
def finish(
    query_id: str,
    request: Request,
):
    query = get_query_from_query_id(request.app.state.QUERY_MANAGER, Query, query_id)

    query.logger.info(f"{query=}")
    if query.status < Status.COMPLETE:
        query.logger.info("calling query finish")
        query.finish()
        return {"message": "Query stopped successfully", "query_id": query_id}
    return {"message": "Query already complete", "query_id": query_id}


@router.post("/kill/{query_id}")
def kill(
    query_id: str,
    request: Request,
):
    query = get_query_from_query_id(request.app.state.QUERY_MANAGER, Query, query_id)

    query.logger.info(f"kill called for {query_id=}")
    if query.status < Status.COMPLETE:
        query.kill()
        return {"message": "Query killed", "query_id": query_id}
    return {"message": "Query already complete", "query_id": query_id}
