"""Drive workspace-specific endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.local_identity import get_local_user_id
from backend.schemas.action import ToolInvokeRequest
from backend.schemas.envelope import ResponseEnvelope
from backend.services.tool_invoke_service import ToolInvokeService

router = APIRouter(prefix="/v1/workspace/drive", tags=["Drive"])


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
async def search_files(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.search_files", body)


@router.post("/upload")
async def upload_file(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.upload_file", body)


@router.post("/move")
async def move_file(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.move_file", body)


@router.post("/copy")
async def copy_file(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.copy_file", body)


@router.post("/share")
async def share_file(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.share_file", body)


@router.post("/delete")
async def delete_file(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.delete_file", body)


@router.post("/export")
async def export_file(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.export_file", body)


@router.post("/content")
async def get_content(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("drive.get_file_content", body)
