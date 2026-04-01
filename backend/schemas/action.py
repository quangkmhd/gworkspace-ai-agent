"""Action and approval schemas matching the agent design spec."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.common import (
    ActionStatus,
    ApprovalStatus,
    RiskLevel,
    TimestampMixin,
    generate_action_id,
    generate_approval_id,
)


class ActionSchema(BaseModel):
    """Standardized action schema per docs/4. AGENT DESIGN.md.

    Every agent action follows this structure for risk control and auditability.
    """

    action_id: str = Field(default_factory=generate_action_id)
    tool: str  # e.g. "gmail.send_email"
    args: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    reason: str = ""
    status: ActionStatus = ActionStatus.PLANNED

    def to_preview(self) -> dict[str, Any]:
        """Generate user-friendly preview for HITL UI."""
        highlights = []
        for key, value in self.args.items():
            if isinstance(value, list):
                highlights.append(f"{key}: {', '.join(str(v) for v in value)}")
            elif isinstance(value, str) and len(value) > 100:
                highlights.append(f"{key}: {value[:100]}...")
            else:
                highlights.append(f"{key}: {value}")
        return {
            "title": f"{self.tool} ({self.risk_level.value} risk)",
            "highlights": highlights[:10],  # Cap at 10 items
        }


class ApprovalPayload(TimestampMixin):
    """HITL approval payload per docs/5. HITL DESIGN.md."""

    approval_id: str = Field(default_factory=generate_approval_id)
    task_id: str = ""
    action: ActionSchema
    preview: dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    user_id: str = ""
    decided_at: float | None = None
    decided_by: str | None = None
    edited_args: dict[str, Any] | None = None
    expires_at: float | None = None
    reason: str = ""


class CreateTaskRequest(BaseModel):
    """POST /v1/agent/tasks request body."""

    user_id: str
    prompt: str
    context: dict[str, Any] = Field(default_factory=dict)


class ToolInvokeRequest(BaseModel):
    """POST /v1/tools/{tool_name}/invoke request body."""

    task_id: str = ""
    actor: str = "user"
    args: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    idempotency_key: str | None = None


class EditApproveRequest(BaseModel):
    """POST /v1/hitl/approvals/{id}/edit-approve request body."""

    edited_args: dict[str, Any]
    reason: str = ""


class RejectRequest(BaseModel):
    """POST /v1/hitl/approvals/{id}/reject request body."""

    reason: str = ""
