"""Integration tests for HITL approval flow."""

from __future__ import annotations

import time

from backend.schemas.action import ActionSchema, ApprovalPayload
from backend.schemas.common import ApprovalStatus, RiskLevel
from hitl.workflow import HITLWorkflow
from tools.registry import ToolRegistry


class TestHITLFlow:
    def setup_method(self):
        ToolRegistry.reset()
        self.workflow = HITLWorkflow()

    def _create_test_proposal(self) -> ApprovalPayload:
        action = ActionSchema(
            tool="gmail.send_email",
            args={"to": ["test@test.com"], "subject": "Test", "body": "Test body"},
            risk_level=RiskLevel.HIGH,
            requires_approval=True,
            reason="Email send is irreversible",
        )
        proposal = ApprovalPayload(
            task_id="tsk_test",
            action=action,
            preview=action.to_preview(),
            user_id="user_test",
            expires_at=time.time() + 3600,
        )
        return self.workflow.create_proposal(proposal)

    def test_create_and_approve(self):
        """Full lifecycle: create → approve → execute."""
        proposal = self._create_test_proposal()
        assert proposal.status == ApprovalStatus.PENDING

        approved = self.workflow.approve(proposal.approval_id, decided_by="reviewer")
        assert approved is not None
        assert approved.status == ApprovalStatus.APPROVED

    def test_create_and_reject(self):
        """Create → reject."""
        proposal = self._create_test_proposal()
        rejected = self.workflow.reject(
            proposal.approval_id, decided_by="reviewer", reason="Not needed"
        )
        assert rejected is not None
        assert rejected.status == ApprovalStatus.REJECTED

    def test_create_and_edit_approve(self):
        """Create → edit-approve with modified args."""
        proposal = self._create_test_proposal()
        edited = self.workflow.edit_approve(
            proposal.approval_id,
            edited_args={"to": ["new@test.com"], "subject": "Edited", "body": "Changed"},
            decided_by="reviewer",
            reason="Changed recipient",
        )
        assert edited is not None
        assert edited.status == ApprovalStatus.EDITED
        assert edited.edited_args is not None

    def test_create_and_cancel(self):
        proposal = self._create_test_proposal()
        cancelled = self.workflow.cancel(proposal.approval_id, decided_by="user")
        assert cancelled is not None
        assert cancelled.status == ApprovalStatus.CANCELLED

    def test_double_approve_fails(self):
        """Approving an already approved proposal should fail."""
        proposal = self._create_test_proposal()
        self.workflow.approve(proposal.approval_id)
        try:
            self.workflow.approve(proposal.approval_id)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected

    def test_list_approvals(self):
        self._create_test_proposal()
        self._create_test_proposal()
        approvals = self.workflow.list_approvals()
        assert len(approvals) >= 2
