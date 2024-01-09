from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form

from ..local_paths import Paths
from ..queries import IPACoordinatorQuery, IPAHelperQuery
from ..query.demo_logger import DemoLoggerQuery
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
    background_tasks: BackgroundTasks,
):
    role = settings.role
    if not role or role == role.COORDINATOR:
        raise Exception("Cannot start helper without helper role.")

    paths = Paths(
        repo_path=settings.root_path / Path("ipa"),
        config_path=settings.config_path,
        commit_hash=commit_hash,
    )
    query = IPAHelperQuery(
        paths=paths,
        query_id=query_id,
        port=settings.helper.helper_port,
    )
    background_tasks.add_task(query.run_all)

    return {"message": "Process started successfully", "query_id": query_id}


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
    role = settings.role
    if role != role.COORDINATOR:
        raise Exception(f"Sidecar {role}: Cannot start query without coordinator role.")

    paths = Paths(
        repo_path=settings.root_path / Path("ipa"),
        config_path=settings.config_path,
        commit_hash=commit_hash,
    )
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
    background_tasks.add_task(query.run_all)

    return {"message": "Process started successfully", "query_id": query_id}
