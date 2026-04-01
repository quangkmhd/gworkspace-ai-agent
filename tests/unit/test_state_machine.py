"""Unit tests for HITL state machine."""

from __future__ import annotations

import pytest

from backend.schemas.common import ApprovalStatus
from hitl.state_machine import StateMachine


class TestStateMachine:
    def test_pending_to_approved(self):
        assert StateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.APPROVED)

    def test_pending_to_rejected(self):
        assert StateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.REJECTED)

    def test_pending_to_edited(self):
        assert StateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.EDITED)

    def test_pending_to_expired(self):
        assert StateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.EXPIRED)

    def test_pending_to_cancelled(self):
        assert StateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.CANCELLED)

    def test_approved_is_terminal(self):
        assert StateMachine.is_terminal(ApprovalStatus.APPROVED)
        assert not StateMachine.can_transition(ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)

    def test_rejected_is_terminal(self):
        assert StateMachine.is_terminal(ApprovalStatus.REJECTED)

    def test_invalid_transition_raises(self):
        with pytest.raises(ValueError, match="Invalid transition"):
            StateMachine.validate_transition(ApprovalStatus.APPROVED, ApprovalStatus.PENDING)

    def test_get_allowed_transitions(self):
        allowed = StateMachine.get_allowed_transitions(ApprovalStatus.PENDING)
        assert ApprovalStatus.APPROVED in allowed
        assert ApprovalStatus.REJECTED in allowed
        assert len(allowed) == 5  # approved, edited, rejected, expired, cancelled
