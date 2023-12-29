import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import APIRouter
from pydantic import BaseModel

from ..helpers import Role
from ..logger import logger
from ..queries import Query, Status
from ..settings import settings

router = APIRouter(
    prefix="/stop",
    tags=[
        "stop",
    ],
)


def validate_query_signature(
    query_id: str,
    identity: int,
    signature: bytes,
) -> bool:
    helpers = settings.helpers
    role = Role(identity)
    helper = helpers[role]
    try:
        helper.public_key.verify(
            signature, query_id.encode("utf8"), ec.ECDSA(hashes.SHA256())
        )
        return True
    except InvalidSignature:
        return False


# pyre-ignore: https://pyre-check.org/docs/errors/#dataclass-like-classes
class SignedRequestModel(BaseModel):
    identity: int
    signature: bytes


@router.post("/finish/{query_id}")
def finish(
    query_id: str,
    data: SignedRequestModel,
):
    identity = data.identity
    signature = base64.b64decode(data.signature)
    logger.info(f"finish called for {query_id=}")
    if not validate_query_signature(query_id, identity, signature):
        logger.warning("signature invalid")
        return {"message": "Invalid signature"}
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
