from typing import Type

from fastapi import HTTPException

from ..query.base import Query, QueryManager


def get_query_from_query_id(
    query_manager: QueryManager,
    query_cls: Type[Query],
    query_id: str,
) -> Query:
    query = query_manager.get_from_query_id(query_cls, query_id)
    if query is None:
        raise HTTPException(status_code=404, detail=f"Query<{query_id}> not found")
    return query


def check_capacity(
    query_manager: QueryManager,
) -> None:
    if not query_manager.capacity_available:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Capacity unavailable. Currently running "
                f"{len(query_manager.running_queries)} of "
                f"{query_manager.max_parallel_queries} queries."
            ),
        )
