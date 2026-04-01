"""Gmail workspace-specific endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.local_identity import get_local_user_id
from backend.schemas.action import ToolInvokeRequest
from backend.schemas.envelope import ResponseEnvelope
from backend.services.tool_invoke_service import ToolInvokeService

router = APIRouter(prefix="/v1/workspace/gmail", tags=["Gmail"])


def _invoke(tool: str, body: ToolInvokeRequest) -> ResponseEnvelope:
    try:
        user_id = get_local_user_id()
        result = ToolInvokeService().invoke(
            tool_name=tool,
            args=body.args,
            task_id=body.task_id,
            actor=user_id,
            dry_run=body.dry_run,
        )
        return ResponseEnvelope.success(data=result)
    except ValueError as e:
        return ResponseEnvelope.fail("INVOKE_ERROR", str(e))


@router.post("/search")
async def gmail_search(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("gmail.search", body)


@router.post("/message")
async def gmail_get_message(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("gmail.get_message", body)


@router.post("/thread")
async def gmail_get_thread(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("gmail.get_thread", body)


@router.post("/draft")
async def gmail_create_draft(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("gmail.create_draft", body)


@router.post("/send")
async def gmail_send(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("gmail.send_email", body)
