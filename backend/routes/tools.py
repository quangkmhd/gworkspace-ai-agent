"""Tools endpoints — list, detail, generic invoke."""

from __future__ import annotations

from fastapi import APIRouter

from backend.config import get_settings
from backend.middleware.auth import CurrentUser
from backend.schemas.action import ToolInvokeRequest
from backend.schemas.envelope import ResponseEnvelope
from backend.services.oauth_service import DEFAULT_SCOPES, OAuthService
from backend.services.token_store import TokenStore
from backend.services.tool_invoke_service import ToolInvokeService
from tools.registry import ToolRegistry

router = APIRouter(prefix="/v1/tools", tags=["Tools"])


@router.get("")
async def list_tools() -> ResponseEnvelope:
    """GET /v1/tools — List all tools with schemas."""
    registry = ToolRegistry.get()
    tools = [t.model_dump() for t in registry.list_tools()]
    return ResponseEnvelope.success(data={"tools": tools, "total": len(tools)})


@router.get("/{tool_name}")
async def get_tool(tool_name: str) -> ResponseEnvelope:
    """GET /v1/tools/{tool_name} — Get tool detail."""
    registry = ToolRegistry.get()
    tool_def = registry.get_tool(tool_name)
    if not tool_def:
        return ResponseEnvelope.fail("TOOL_NOT_FOUND", f"Tool '{tool_name}' not found")
    return ResponseEnvelope.success(data=tool_def.model_dump())


@router.post("/{tool_name}/invoke")
async def invoke_tool(
    tool_name: str,
    body: ToolInvokeRequest,
    user: CurrentUser,
) -> ResponseEnvelope:
    """POST /v1/tools/{tool_name}/invoke — Generic invoke with policy/HITL gate."""
    try:
        settings = get_settings()
        user_id = user or "anonymous"
        token_data = TokenStore().get(user_id)
        granted_scopes = token_data.get("scopes", []) if token_data else []
        if settings.MOCK_MODE and not token_data:
            granted_scopes = DEFAULT_SCOPES
        credentials = OAuthService().get_credentials(token_data) if token_data else None

        service = ToolInvokeService()
        result = service.invoke(
            tool_name=tool_name,
            args=body.args,
            task_id=body.task_id,
            actor=user_id,
            dry_run=body.dry_run,
            credentials=credentials,
            granted_scopes=granted_scopes,
        )
        return ResponseEnvelope.success(data=result)
    except ValueError as e:
        return ResponseEnvelope.fail("INVOKE_ERROR", str(e))
    except Exception as e:
        return ResponseEnvelope.fail("INTERNAL_ERROR", str(e))
