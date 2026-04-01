"""Agent schemas — Pydantic models for agent state, plans, and proposals."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.common import (
    ActionStatus,
    RiskLevel,
    TaskStatus,
    TimestampMixin,
    generate_action_id,
    generate_task_id,
)


class PlanStep(BaseModel):
    """A single step in an agent task plan."""

    step: int
    goal: str
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[int] = Field(default_factory=list)


class TaskPlan(BaseModel):
    """Agent's structured plan for a task."""

    task_id: str = Field(default_factory=generate_task_id)
    intent: str = ""
    steps: list[PlanStep] = Field(default_factory=list)


class ActionProposal(BaseModel):
    """An action the agent proposes to take."""

    action_id: str = Field(default_factory=generate_action_id)
    step: int = 0
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    reason: str = ""
    status: ActionStatus = ActionStatus.PLANNED
    result: dict[str, Any] | None = None
    error: str | None = None


class AgentState(BaseModel):
    """Agent execution state — tracked through LangGraph."""

    task_id: str = Field(default_factory=generate_task_id)
    user_id: str = ""
    prompt: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.CREATED
    plan: TaskPlan | None = None
    actions: list[ActionProposal] = Field(default_factory=list)
    current_step: int = 0
    results: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class TaskResponse(TimestampMixin):
    """Response returned to API for a task."""

    task_id: str
    status: TaskStatus
    plan: TaskPlan | None = None
    actions: list[ActionProposal] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
