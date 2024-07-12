from fastapi import APIRouter, HTTPException, Request

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
    request: Request,
):
    query_manager = request.app.state.QUERY_MANAGER
    query = query_manager.get_from_query_id(Query, query_id)
    if query is None:
        raise HTTPException(status_code=404, detail="Query not found")

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
    query_manager = request.app.state.QUERY_MANAGER
    query = query_manager.get_from_query_id(Query, query_id)
    if query is None:
        raise HTTPException(status_code=404, detail="Query not found")

    query.logger.info(f"kill called for {query_id=}")
    if query.status < Status.COMPLETE:
        query.kill()
        return {"message": "Query killed", "query_id": query_id}
    return {"message": "Query already complete", "query_id": query_id}
