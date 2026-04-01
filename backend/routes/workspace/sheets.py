"""Sheets workspace-specific endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.local_identity import get_local_user_id
from backend.schemas.action import ToolInvokeRequest
from backend.schemas.envelope import ResponseEnvelope
from backend.services.tool_invoke_service import ToolInvokeService

router = APIRouter(prefix="/v1/workspace/sheets", tags=["Sheets"])


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


@router.post("/create")
async def create_spreadsheet(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.create_spreadsheet", body)


@router.post("/info")
async def get_info(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.get_spreadsheet_info", body)


@router.post("/read")
async def read_data(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.read_data", body)


@router.post("/batch-read")
async def batch_read(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.batch_read_data", body)


@router.post("/filtered-read")
async def filtered_read(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.filtered_read_data", body)


@router.post("/update")
async def update_values(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.update_values", body)


@router.post("/append")
async def append_values(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.append_values", body)


@router.post("/clear")
async def clear_values(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("sheets.clear_values", body)
