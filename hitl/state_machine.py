"""HITL state machine — manages approval state transitions.

States: pending → approved / edited / rejected / expired / cancelled
"""

from __future__ import annotations

from typing import Any

import structlog

from backend.schemas.common import ApprovalStatus

logger = structlog.get_logger("hitl.state_machine")

# Valid state transitions
TRANSITIONS: dict[ApprovalStatus, set[ApprovalStatus]] = {
    ApprovalStatus.PENDING: {
        ApprovalStatus.APPROVED,
        ApprovalStatus.EDITED,
        ApprovalStatus.REJECTED,
        ApprovalStatus.EXPIRED,
        ApprovalStatus.CANCELLED,
    },
    ApprovalStatus.APPROVED: set(),  # Terminal
    ApprovalStatus.EDITED: set(),    # Terminal
    ApprovalStatus.REJECTED: set(),  # Terminal
    ApprovalStatus.EXPIRED: set(),   # Terminal
    ApprovalStatus.CANCELLED: set(), # Terminal
}


class StateMachine:
    """Validates and executes HITL approval state transitions."""

    @staticmethod
    def can_transition(current: ApprovalStatus, target: ApprovalStatus) -> bool:
        """Check if a transition is valid."""
        allowed = TRANSITIONS.get(current, set())
        return target in allowed

    @staticmethod
    def validate_transition(current: ApprovalStatus, target: ApprovalStatus) -> None:
        """Validate transition, raise ValueError if invalid."""
        if not StateMachine.can_transition(current, target):
            raise ValueError(
                f"Invalid transition: {current.value} → {target.value}. "
                f"Allowed: {[s.value for s in TRANSITIONS.get(current, set())]}"
            )

    @staticmethod
    def is_terminal(status: ApprovalStatus) -> bool:
        """Check if a status is terminal (no further transitions)."""
        return len(TRANSITIONS.get(status, set())) == 0

    @staticmethod
    def get_allowed_transitions(current: ApprovalStatus) -> list[ApprovalStatus]:
        """Get list of valid next states."""
        return list(TRANSITIONS.get(current, set()))
