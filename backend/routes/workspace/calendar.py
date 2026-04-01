"""Calendar workspace-specific endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.local_identity import get_local_user_id
from backend.schemas.action import ToolInvokeRequest
from backend.schemas.envelope import ResponseEnvelope
from backend.services.tool_invoke_service import ToolInvokeService

router = APIRouter(prefix="/v1/workspace/calendar", tags=["Calendar"])


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


@router.post("/calendars")
async def get_calendars(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("calendar.get_calendars_info", body)


@router.post("/events/search")
async def search_events(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("calendar.search_events", body)


@router.post("/events/create")
async def create_event(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("calendar.create_event", body)


@router.post("/events/update")
async def update_event(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("calendar.update_event", body)


@router.post("/events/move")
async def move_event(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("calendar.move_event", body)


@router.post("/events/delete")
async def delete_event(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("calendar.delete_event", body)


@router.post("/datetime")
async def get_datetime(body: ToolInvokeRequest) -> ResponseEnvelope:
    return _invoke("calendar.get_current_datetime", body)
