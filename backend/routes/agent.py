"""Agent task endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.middleware.auth import CurrentUser
from backend.schemas.action import CreateTaskRequest
from backend.schemas.envelope import ResponseEnvelope
from backend.services.agent_service import AgentService

router = APIRouter(prefix="/v1/agent", tags=["Agent"])

# Singleton service (in production, use DI)
_service = AgentService()


@router.post("/tasks")
async def create_task(body: CreateTaskRequest, user: CurrentUser) -> ResponseEnvelope:
    """POST /v1/agent/tasks — Create task from prompt."""
    try:
        response = _service.create_task(
            user_id=body.user_id,
            prompt=body.prompt,
            context=body.context,
        )
        return ResponseEnvelope.success(data=response.model_dump())
    except Exception as e:
        return ResponseEnvelope.fail("TASK_ERROR", str(e))


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, user: CurrentUser) -> ResponseEnvelope:
    """GET /v1/agent/tasks/{task_id} — Get task status/plan."""
    response = _service.get_task(task_id)
    if not response:
        return ResponseEnvelope.fail("NOT_FOUND", f"Task {task_id} not found")
    return ResponseEnvelope.success(data=response.model_dump())


@router.get("/tasks/{task_id}/actions")
async def get_task_actions(task_id: str, user: CurrentUser) -> ResponseEnvelope:
    """GET /v1/agent/tasks/{task_id}/actions — List actions."""
    actions = _service.get_task_actions(task_id)
    return ResponseEnvelope.success(data={"actions": actions, "total": len(actions)})


@router.get("/actions/{action_id}")
async def get_action(action_id: str, user: CurrentUser) -> ResponseEnvelope:
    """GET /v1/agent/actions/{action_id} — Action detail."""
    action = _service.get_action(action_id)
    if not action:
        return ResponseEnvelope.fail("NOT_FOUND", f"Action {action_id} not found")
    return ResponseEnvelope.success(data=action)
