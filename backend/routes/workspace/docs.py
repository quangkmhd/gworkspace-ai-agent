"""Docs workspace-specific endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.middleware.auth import CurrentUser
from backend.schemas.action import ToolInvokeRequest
from backend.schemas.envelope import ResponseEnvelope
from backend.services.tool_invoke_service import ToolInvokeService

router = APIRouter(prefix="/v1/workspace/docs", tags=["Docs"])


def _invoke(tool: str, body: ToolInvokeRequest) -> ResponseEnvelope:
    try:
        result = ToolInvokeService().invoke(
            tool_name=tool, args=body.args, task_id=body.task_id, actor=body.actor, dry_run=body.dry_run,
        )
        return ResponseEnvelope.success(data=result)
    except ValueError as e:
        return ResponseEnvelope.fail("INVOKE_ERROR", str(e))


@router.post("/create")
async def create_document(body: ToolInvokeRequest, user: CurrentUser) -> ResponseEnvelope:
    return _invoke("docs.create_document", body)


@router.post("/get")
async def get_document(body: ToolInvokeRequest, user: CurrentUser) -> ResponseEnvelope:
    return _invoke("docs.get_document", body)


@router.post("/batch-update")
async def batch_update(body: ToolInvokeRequest, user: CurrentUser) -> ResponseEnvelope:
    return _invoke("docs.batch_update", body)


@router.post("/insert-text")
async def insert_text(body: ToolInvokeRequest, user: CurrentUser) -> ResponseEnvelope:
    return _invoke("docs.insert_text", body)


@router.post("/replace-text")
async def replace_text(body: ToolInvokeRequest, user: CurrentUser) -> ResponseEnvelope:
    return _invoke("docs.replace_text", body)


@router.post("/share")
async def share_document(body: ToolInvokeRequest, user: CurrentUser) -> ResponseEnvelope:
    return _invoke("docs.share_document", body)
