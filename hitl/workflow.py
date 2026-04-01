"""HITL workflow — orchestrates: create proposal → wait for decision → execute or cancel → log."""

from __future__ import annotations

from typing import Any

import structlog

from backend.schemas.action import ActionSchema, ApprovalPayload
from backend.schemas.common import ApprovalStatus
from hitl.audit import AuditLogger
from hitl.queue import ApprovalQueue
from hitl.state_machine import StateMachine
from tools.registry import ToolRegistry

logger = structlog.get_logger("hitl.workflow")


class HITLWorkflow:
    """Orchestrates the complete HITL approval workflow."""

    def __init__(self) -> None:
        self._queue = ApprovalQueue()
        self._audit = AuditLogger()
        self._registry = ToolRegistry.get()

    def create_proposal(self, proposal: ApprovalPayload) -> ApprovalPayload:
        """Create a new approval proposal and log it."""
        created = self._queue.create(proposal)
        self._audit.log_event(
            event_type="proposal_created",
            task_id=proposal.task_id,
            action_id=proposal.action.action_id,
            approval_id=proposal.approval_id,
            actor="system",
            details={"tool": proposal.action.tool, "risk_level": proposal.action.risk_level.value},
        )
        return created

    def approve(self, approval_id: str, decided_by: str = "") -> ApprovalPayload | None:
        """Approve a proposal and execute the action."""
        proposal = self._queue.get(approval_id)
        if not proposal:
            return None

        StateMachine.validate_transition(proposal.status, ApprovalStatus.APPROVED)
        updated = self._queue.update_status(approval_id, ApprovalStatus.APPROVED, decided_by=decided_by)

        self._audit.log_event(
            event_type="proposal_approved",
            task_id=proposal.task_id,
            action_id=proposal.action.action_id,
            approval_id=approval_id,
            actor=decided_by,
        )

        # Execute the approved action
        if updated:
            self._execute_action(updated)

        return updated

    def edit_approve(
        self,
        approval_id: str,
        edited_args: dict[str, Any],
        decided_by: str = "",
        reason: str = "",
    ) -> ApprovalPayload | None:
        """Approve with edited arguments."""
        proposal = self._queue.get(approval_id)
        if not proposal:
            return None

        StateMachine.validate_transition(proposal.status, ApprovalStatus.EDITED)
        updated = self._queue.update_status(
            approval_id,
            ApprovalStatus.EDITED,
            decided_by=decided_by,
            edited_args=edited_args,
            reason=reason,
        )

        self._audit.log_event(
            event_type="proposal_edit_approved",
            task_id=proposal.task_id,
            action_id=proposal.action.action_id,
            approval_id=approval_id,
            actor=decided_by,
            details={"edited_args": edited_args, "reason": reason},
        )

        # Execute with edited args
        if updated:
            self._execute_action(updated, args_override=edited_args)

        return updated

    def reject(
        self, approval_id: str, decided_by: str = "", reason: str = ""
    ) -> ApprovalPayload | None:
        """Reject a proposal."""
        proposal = self._queue.get(approval_id)
        if not proposal:
            return None

        StateMachine.validate_transition(proposal.status, ApprovalStatus.REJECTED)
        updated = self._queue.update_status(
            approval_id, ApprovalStatus.REJECTED, decided_by=decided_by, reason=reason,
        )

        self._audit.log_event(
            event_type="proposal_rejected",
            task_id=proposal.task_id,
            action_id=proposal.action.action_id,
            approval_id=approval_id,
            actor=decided_by,
            details={"reason": reason},
        )

        return updated

    def cancel(self, approval_id: str, decided_by: str = "") -> ApprovalPayload | None:
        """Cancel a proposal."""
        proposal = self._queue.get(approval_id)
        if not proposal:
            return None

        StateMachine.validate_transition(proposal.status, ApprovalStatus.CANCELLED)
        updated = self._queue.update_status(
            approval_id, ApprovalStatus.CANCELLED, decided_by=decided_by,
        )

        self._audit.log_event(
            event_type="proposal_cancelled",
            task_id=proposal.task_id,
            action_id=proposal.action.action_id,
            approval_id=approval_id,
            actor=decided_by,
        )

        return updated

    def _execute_action(
        self,
        proposal: ApprovalPayload,
        args_override: dict[str, Any] | None = None,
    ) -> None:
        """Execute an approved action."""
        args = args_override or proposal.action.args
        tool_name = proposal.action.tool

        try:
            result = self._registry.invoke(tool_name, args)
            self._audit.log_event(
                event_type="action_executed",
                task_id=proposal.task_id,
                action_id=proposal.action.action_id,
                approval_id=proposal.approval_id,
                actor="system",
                details={"tool": tool_name, "result_keys": list(result.keys())},
            )
            logger.info("action_executed_after_approval", tool=tool_name, approval_id=proposal.approval_id)
        except Exception as e:
            self._audit.log_event(
                event_type="action_execution_failed",
                task_id=proposal.task_id,
                action_id=proposal.action.action_id,
                approval_id=proposal.approval_id,
                actor="system",
                details={"error": str(e)},
            )
            logger.error("action_execution_failed", tool=tool_name, error=str(e))

    def list_approvals(
        self,
        user_id: str | None = None,
        status: ApprovalStatus | None = None,
        limit: int = 50,
    ) -> list[ApprovalPayload]:
        """List approvals with filters."""
        return self._queue.list_approvals(user_id=user_id, status=status, limit=limit)

    def get_approval(self, approval_id: str) -> ApprovalPayload | None:
        """Get approval detail."""
        return self._queue.get(approval_id)
