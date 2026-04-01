"""Agent service — manages task lifecycle, invokes agent, stores results."""

from __future__ import annotations

import time
from typing import Any

import structlog

from agent.executor import AgentExecutor
from agent.planner import Planner
from agent.schemas import AgentState, TaskResponse
from backend.schemas.common import TaskStatus, generate_task_id

logger = structlog.get_logger("agent_service")


class AgentService:
    """Manages the full lifecycle of agent tasks."""

    def __init__(self) -> None:
        self._planner = Planner()
        self._executor = AgentExecutor()
        # In-memory task store (SQLite in production)
        self._tasks: dict[str, AgentState] = {}

    def create_task(
        self,
        user_id: str,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> TaskResponse:
        """Create a new agent task from user prompt.

        1. Generate plan via LLM
        2. Execute plan with HITL gates
        3. Return task response
        """
        task_id = generate_task_id()

        # Create plan
        plan = self._planner.create_plan(
            user_input=prompt,
            user_id=user_id,
            context=context,
        )
        plan.task_id = task_id

        # Build state
        state = AgentState(
            task_id=task_id,
            user_id=user_id,
            prompt=prompt,
            context=context or {},
            status=TaskStatus.PLANNING,
            plan=plan,
        )

        # Execute
        state = self._executor.execute_plan(state)

        # Store
        self._tasks[task_id] = state

        return self._to_response(state)

    def get_task(self, task_id: str) -> TaskResponse | None:
        """Get task status by ID."""
        state = self._tasks.get(task_id)
        if not state:
            return None
        return self._to_response(state)

    def get_task_actions(self, task_id: str) -> list[dict[str, Any]]:
        """Get all actions for a task."""
        state = self._tasks.get(task_id)
        if not state:
            return []
        return [a.model_dump() for a in state.actions]

    def get_action(self, action_id: str) -> dict[str, Any] | None:
        """Get action detail by ID."""
        for state in self._tasks.values():
            for action in state.actions:
                if action.action_id == action_id:
                    return action.model_dump()
        return None

    def resume_task(
        self,
        task_id: str,
        approved_action_ids: list[str],
        edited_args: dict[str, dict[str, Any]] | None = None,
    ) -> TaskResponse | None:
        """Resume a task after HITL approval."""
        state = self._tasks.get(task_id)
        if not state:
            return None

        state = self._executor.resume_after_approval(state, approved_action_ids, edited_args)
        self._tasks[task_id] = state
        return self._to_response(state)

    def list_tasks(
        self,
        user_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int = 20,
    ) -> list[TaskResponse]:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())
        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return [self._to_response(t) for t in tasks[:limit]]

    @staticmethod
    def _to_response(state: AgentState) -> TaskResponse:
        return TaskResponse(
            task_id=state.task_id,
            status=state.status,
            plan=state.plan,
            actions=state.actions,
            results=state.results,
            error=state.error,
        )
