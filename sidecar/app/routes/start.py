from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form

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

    local_ipa_path = settings.root_path / Path("ipa")
    query = IPAHelperQuery(
        query_id=query_id,
        local_ipa_path=local_ipa_path,
        config_path=settings.config_path,
        commit_hash="dcb6a391309f9c58defd231029f8df489728f225",
    )

    query.run_in_thread()

    return {"message": "Process started successfully", "query_id": query_id}


@router.post("/ipa-query/{query_id}")
def start_ipa_test_query(
    query_id: str,
):
    role = settings.role
    if role != role.COORDINATOR:
        raise Exception(f"Sidecar {role}: Cannot start query without coordinator role.")

    local_ipa_path = settings.root_path / Path("ipa")
    test_data_path = local_ipa_path / Path("test_data/input")
    size = 1000
    query = IPACoordinatorQuery(
        query_id=query_id,
        local_ipa_path=local_ipa_path,
        test_data_path=test_data_path,
        test_data_file=test_data_path / Path(f"events-{size}.txt"),
        config_path=settings.config_path,
        size=size,
        max_breakdown_key=256,
        max_trigger_value=7,
        per_user_credit_cap=16,
        commit_hash="dcb6a391309f9c58defd231029f8df489728f225",
    )

    query.run_in_thread()

    return {"message": "Process started successfully", "query_id": query_id}
