from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form

from ..local_paths import Paths
from ..logger import logger
from ..queries import DemoLoggerQuery, IPACoordinatorQuery, IPAHelperQuery
from ..settings import settings

router = APIRouter(
    prefix="/start",
    tags=[
        "start",
    ],
)


@router.post("/demo-logger/{query_id}")
def demo_logger(
    query_id: str,
    num_lines: Annotated[int, Form()],
    total_runtime: Annotated[int, Form()],
):
    query = DemoLoggerQuery(
        query_id=query_id,
        num_lines=num_lines,
        total_runtime=total_runtime,
    )
    query.run_in_thread()

    return {"message": "Process started successfully", "query_id": query_id}


@router.post("/ipa-helper/{query_id}")
def start_ipa_helper(query_id: str):
    role = settings.role
    if not role or role == role.COORDINATOR:
        raise Exception("Cannot start helper without helper role.")

    paths = Paths(
        repo_path=settings.root_path / Path("ipa"),
        config_path=settings.config_path,
        commit_hash="dcb6a391309f9c58defd231029f8df489728f225",
    )
    query = IPAHelperQuery(
        paths=paths,
        query_id=query_id,
    )

    query.run_in_thread()

    return {"message": "Process started successfully", "query_id": query_id}


@router.post("/ipa-query/{query_id}")
def start_ipa_test_query(
    query_id: str,
    size: Annotated[int, Form()],
    max_breakdown_key: Annotated[int, Form()],
    max_trigger_value: Annotated[int, Form()],
    per_user_credit_cap: Annotated[int, Form()],
):
    role = settings.role
    if role != role.COORDINATOR:
        raise Exception(f"Sidecar {role}: Cannot start query without coordinator role.")

    paths = Paths(
        repo_path=settings.root_path / Path("ipa"),
        config_path=settings.config_path,
        commit_hash="dcb6a391309f9c58defd231029f8df489728f225",
    )
    logger.warning((size, max_breakdown_key, max_trigger_value, per_user_credit_cap))
    test_data_path = paths.repo_path / Path("test_data/input")
    query = IPACoordinatorQuery(
        query_id=query_id,
        paths=paths,
        test_data_file=test_data_path / Path(f"events-{size}.txt"),
        size=size,
        max_breakdown_key=max_breakdown_key,
        max_trigger_value=max_trigger_value,
        per_user_credit_cap=per_user_credit_cap,
    )

    query.run_in_thread()

    return {"message": "Process started successfully", "query_id": query_id}
