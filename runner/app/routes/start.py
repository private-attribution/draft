from typing import Annotated
from fastapi import APIRouter, Form
from ..processes import QuerySteps, Query
from ..settings import settings


router = APIRouter(
    prefix="/start",
    tags=[
        "start",
    ],
)


@router.post("/demo-logger/{process_id}")
def demo_logger(
    process_id: str,
    num_lines: Annotated[int, Form()],
    total_runtime: Annotated[int, Form()],
):
    query = Query(
        query_id=process_id,
        steps=QuerySteps["demo-logger"],
    )
    query.run_in_thread(
        num_lines=num_lines,
        total_runtime=total_runtime,
    )

    return {"message": "Process started successfully", "process_id": process_id}


@router.post("/start-ipa-helper/{process_id}")
def start_ipa_helper(process_id: str):
    role = settings.role
    if not role or role.COORDINATOR:
        raise Exception("Cannot start helper without helper role.")
    cmd = f"""
    .venv/bin/helper-cli start-isolated-helper {settings.role.value}
    """
    # start_process(shlex.split(cmd), process_id=process_id)
    return {"message": "Process started successfully", "process_id": process_id}


@router.post("/start-ipa-query/{process_id}")
def start_ipa_test_query(
    process_id: str,
    size: Annotated[int, Form()],
):
    role = settings.role
    if not role or not role.COORDINATOR:
        raise Exception("Cannot start query without coordinator role.")

    cmd = """
    .venv/bin/helper-cli start-isolated-ipa
    """
    # start_process(shlex.split(cmd), process_id=process_id)
    return {"message": "Process started successfully", "process_id": process_id}
