from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Form
from ..queries import QuerySteps, Query
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
    query = Query(
        query_id=query_id,
        steps=QuerySteps["demo-logger"],
    )
    query.run_in_thread(
        num_lines=num_lines,
        total_runtime=total_runtime,
    )

    return {"message": "Process started successfully", "query_id": query_id}


@router.post("/ipa-helper/{query_id}")
def start_ipa_helper(query_id: str):
    role = settings.role
    if not role or role == role.COORDINATOR:
        raise Exception("Cannot start helper without helper role.")

    query = Query(
        query_id=query_id,
        steps=QuerySteps["ipa-helper"],
    )
    local_ipa_path = settings.root_path / Path("ipa")
    query.run_in_thread(
        local_ipa_path=local_ipa_path,
        config_path=settings.config_path,
        branch="main",
        commit_hash="dcb6a391309f9c58defd231029f8df489728f225",
        identity=role.value,
    )

    return {"message": "Process started successfully", "query_id": query_id}


@router.post("/ipa-query/{query_id}")
def start_ipa_test_query(
    query_id: str,
):
    role = settings.role
    if role != role.COORDINATOR:
        raise Exception(f"Sidecar {role}: Cannot start query without coordinator role.")

    query = Query(
        query_id=query_id,
        steps=QuerySteps["ipa-coordinator"],
    )
    size = 1000
    max_breakdown_key = 256
    per_user_credit_cap = 16
    local_ipa_path = settings.root_path / Path("ipa")
    test_data_path = local_ipa_path / Path("test_data/input")
    test_data_file = test_data_path / Path(f"events-{size}.txt")
    query.run_in_thread(
        local_ipa_path=local_ipa_path,
        config_path=settings.config_path,
        commit_hash="dcb6a391309f9c58defd231029f8df489728f225",
        branch="main",
        size=size,
        max_breakdown_key=max_breakdown_key,
        per_user_credit_cap=per_user_credit_cap,
        test_data_path=test_data_path,
        test_data_file=test_data_file,
        query_id=query_id
    )

    return {"message": "Process started successfully", "query_id": query_id}
