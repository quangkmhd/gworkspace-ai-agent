"""Unit tests for policy engine."""

from __future__ import annotations

from backend.schemas.common import RiskLevel
from backend.services.policy_service import PolicyService


class TestPolicyService:
    def setup_method(self):
        self.policy = PolicyService()

    def test_low_risk_no_hitl(self):
        result = self.policy.evaluate("gmail.search")
        assert result["risk_level"] == RiskLevel.LOW
        assert result["requires_approval"] is False

    def test_high_risk_requires_hitl(self):
        result = self.policy.evaluate("gmail.send_email")
        assert result["risk_level"] == RiskLevel.HIGH
        assert result["requires_approval"] is True

    def test_medium_risk_no_hitl(self):
        result = self.policy.evaluate("gmail.create_draft")
        assert result["risk_level"] == RiskLevel.MEDIUM
        assert result["requires_approval"] is False

    def test_always_hitl_for_delete(self):
        assert self.policy.requires_hitl("calendar.delete_event") is True
        assert self.policy.requires_hitl("drive.delete_file") is True

    def test_always_hitl_for_share(self):
        assert self.policy.requires_hitl("drive.share_file") is True
        assert self.policy.requires_hitl("docs.share_document") is True

    def test_scope_check_pass(self):
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        assert self.policy.check_scopes("gmail.search", scopes) is True

    def test_scope_check_fail(self):
        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        assert self.policy.check_scopes("gmail.search", scopes) is False
