"""Tool invoke service — orchestrates: validate args → check policy → check HITL → execute/queue."""

from __future__ import annotations

import time
from typing import Any

import structlog

from backend.config import get_settings
from backend.schemas.action import ActionSchema, ApprovalPayload
from backend.schemas.common import ActionStatus, RiskLevel, generate_action_id
from backend.services.policy_service import PolicyService
from hitl.workflow import HITLWorkflow
from tools.registry import ToolRegistry

logger = structlog.get_logger("tool_invoke")


class ToolInvokeService:
    """Orchestrates tool invocation with policy and HITL gates."""

    def __init__(self) -> None:
        self._registry = ToolRegistry.get()
        self._policy = PolicyService()
        self._hitl = HITLWorkflow()

    def invoke(
        self,
        tool_name: str,
        args: dict[str, Any],
        *,
        task_id: str = "",
        actor: str = "user",
        dry_run: bool = False,
        credentials: Any = None,
        granted_scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Full tool invocation flow.

        1. Validate tool exists and args are valid
        2. Evaluate policy (risk, scopes, HITL)
        3. If dry_run → return action preview
        4. If HITL required → create proposal (returned for approval)
        5. Execute tool
        """
        # 1. Validate tool exists
        tool_def = self._registry.get_tool(tool_name)
        if not tool_def:
            raise ValueError(f"Unknown tool: {tool_name}")

        # 2. Validate args
        errors = self._registry.validate_args(tool_name, args)
        if errors:
            raise ValueError(f"Invalid args: {'; '.join(errors)}")

        # 3. Policy evaluation
        policy = self._policy.evaluate(tool_name, granted_scopes)
        if not policy["scopes_ok"]:
            return {
                "status": "scope_error",
                "error": policy["reason"],
                "required_scopes": self._policy.get_required_scopes(tool_name),
            }

        # 4. Build action
        action = ActionSchema(
            action_id=generate_action_id(),
            tool=tool_name,
            args=args,
            risk_level=policy["risk_level"],
            requires_approval=policy["requires_approval"],
            reason=policy.get("reason", ""),
        )

        # 5. Dry run returns preview
        if dry_run:
            return {
                "status": "preview",
                "action": action.model_dump(),
                "preview": action.to_preview(),
                "policy": policy,
            }

        # 6. HITL gate
        if policy["requires_approval"]:
            proposal = ApprovalPayload(
                task_id=task_id,
                action=action,
                preview=action.to_preview(),
                user_id=actor,
                expires_at=time.time() + get_settings().HITL_APPROVAL_TIMEOUT_SECONDS,
            )
            created = self._hitl.create_proposal(proposal)
            return {
                "status": "pending_approval",
                "approval": created.model_dump(),
            }

        # 7. Execute
        try:
            result = self._registry.invoke(tool_name, args, credentials)
            action.status = ActionStatus.COMPLETED
            return {
                "status": "completed",
                "action_id": action.action_id,
                "result": result,
            }
        except Exception as e:
            logger.error("tool_execution_failed", tool=tool_name, error=str(e))
            action.status = ActionStatus.FAILED
            return {
                "status": "failed",
                "action_id": action.action_id,
                "error": str(e),
            }
