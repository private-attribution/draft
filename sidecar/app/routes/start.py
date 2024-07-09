import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException
from fastapi.responses import StreamingResponse

from ..local_paths import Paths
from ..query.base import Query
from ..query.demo_logger import DemoLoggerQuery
from ..query.ipa import GateType, IPACoordinatorQuery, IPAHelperQuery
from ..query.status import Status
from ..settings import get_settings

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
    background_tasks: BackgroundTasks,
):
    query = DemoLoggerQuery(
        query_id=query_id,
        num_lines=num_lines,
        total_runtime=total_runtime,
    )
    background_tasks.add_task(query.start)

    return {"message": "Process started successfully", "query_id": query_id}


@router.post("/ipa-helper/{query_id}")
def start_ipa_helper(
    query_id: str,
    commit_hash: Annotated[str, Form()],
    gate_type: Annotated[str, Form()],
    stall_detection: Annotated[bool, Form()],
    multi_threading: Annotated[bool, Form()],
    disable_metrics: Annotated[bool, Form()],
    background_tasks: BackgroundTasks,
):
    # pylint: disable=too-many-arguments
    settings = get_settings()
    role = settings.role
    if not role or role == role.COORDINATOR:
        raise Exception("Cannot start helper without helper role.")

    compiled_id = (
        f"{commit_hash}_{gate_type}"
        f"{'_stall-detection' if stall_detection else ''}"
        f"{'_multi-threading' if multi_threading else ''}"
        f"{'_disable-metrics' if disable_metrics else ''}"
    )

    paths = Paths(
        repo_path=settings.root_path / Path("ipa"),
        config_path=settings.config_path,
        compiled_id=compiled_id,
    )
    query = IPAHelperQuery(
        paths=paths,
        commit_hash=commit_hash,
        query_id=query_id,
        gate_type=GateType[gate_type.upper()],
        stall_detection=stall_detection,
        multi_threading=multi_threading,
        disable_metrics=disable_metrics,
        port=settings.helper_port,
    )
    background_tasks.add_task(query.start)

    return {"message": "Process started successfully", "query_id": query_id}


@router.get("/ipa-helper/{query_id}/status")
def get_ipa_helper_status(
    query_id: str,
):
    query = Query.get_from_query_id(query_id)
    if query is None:
        return {"status": Status.NOT_FOUND.name}
    return {"status": query.status.name}


@router.get("/{query_id}/log-file")
def get_ipa_helper_log_file(
    query_id: str,
):
    settings = get_settings()
    query = Query.get_from_query_id(query_id)
    if query is None:
        return HTTPException(status_code=404, detail="Query not found")

    def iterfile():
        with open(query.log_file_path, "rb") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    d = datetime.fromtimestamp(
                        float(data["record"]["time"]["timestamp"])
                    )
                    message = data["record"]["message"]
                    yield f"{d.isoformat()} - {message}\n"
                except (json.JSONDecodeError, KeyError):
                    yield line

    return StreamingResponse(
        iterfile(),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{query_id}-{settings.role.name.title()}.log"'
            )
        },
        media_type="text/plain",
    )


@router.post("/ipa-query/{query_id}")
def start_ipa_test_query(
    query_id: str,
    commit_hash: Annotated[str, Form()],
    size: Annotated[int, Form()],
    max_breakdown_key: Annotated[int, Form()],
    max_trigger_value: Annotated[int, Form()],
    per_user_credit_cap: Annotated[int, Form()],
    background_tasks: BackgroundTasks,
):
    # pylint: disable=too-many-arguments
    settings = get_settings()
    role = settings.role
    if role != role.COORDINATOR:
        raise Exception(f"Sidecar {role}: Cannot start query without coordinator role.")

    paths = Paths(
        repo_path=settings.root_path / Path("ipa"),
        config_path=settings.config_path,
        compiled_id=commit_hash,
    )
    test_data_path = paths.repo_path / Path("test_data/input")
    query = IPACoordinatorQuery(
        query_id=query_id,
        paths=paths,
        commit_hash=commit_hash,
        test_data_file=test_data_path / Path(f"events-{size}.txt"),
        size=size,
        max_breakdown_key=max_breakdown_key,
        max_trigger_value=max_trigger_value,
        per_user_credit_cap=per_user_credit_cap,
    )
    background_tasks.add_task(query.start)

    return {"message": "Process started successfully", "query_id": query_id}
