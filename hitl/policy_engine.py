"""HITL policy engine — evaluates tool risk × policy config → requires_approval."""

from __future__ import annotations

from typing import Any

import structlog

from backend.schemas.common import RiskLevel
from backend.services.policy_service import PolicyService

logger = structlog.get_logger("hitl.policy")


class HITLPolicyEngine:
    """Determines whether an action requires human approval.

    Wraps PolicyService to provide HITL-specific evaluation.
    """

    def __init__(self) -> None:
        self._policy = PolicyService()

    def evaluate(self, tool_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Evaluate whether an action requires HITL approval.

        Returns:
            dict with: requires_approval, risk_level, reason, auto_executable
        """
        risk = self._policy.get_risk_level(tool_name)
        requires = self._policy.requires_hitl(tool_name)

        reason = ""
        if requires:
            if risk == RiskLevel.HIGH:
                reason = f"{tool_name} is high risk and requires human approval before execution"
            else:
                reason = f"{tool_name} is configured to require approval"

        return {
            "requires_approval": requires,
            "risk_level": risk,
            "reason": reason,
            "auto_executable": not requires,
        }

    def should_approve_batch(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate a batch of actions.

        Returns summary of which actions need approval.
        """
        results = []
        needs_approval = []
        auto_execute = []

        for action in actions:
            tool = action.get("tool", "")
            eval_result = self.evaluate(tool, action.get("args"))
            results.append({**eval_result, "tool": tool, "action_id": action.get("action_id", "")})
            if eval_result["requires_approval"]:
                needs_approval.append(action)
            else:
                auto_execute.append(action)

        return {
            "total": len(actions),
            "needs_approval": len(needs_approval),
            "auto_execute": len(auto_execute),
            "details": results,
        }
