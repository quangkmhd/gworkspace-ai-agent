"""Unit tests for risk evaluator."""

from __future__ import annotations

from agent.risk_evaluator import RiskEvaluator
from backend.schemas.common import RiskLevel


class TestRiskEvaluator:
    def setup_method(self):
        self.evaluator = RiskEvaluator()

    def test_low_risk_read_only(self):
        result = self.evaluator.evaluate("gmail.search")
        assert result["risk_level"] == RiskLevel.LOW
        assert result["requires_approval"] is False

    def test_medium_risk_reversible_write(self):
        result = self.evaluator.evaluate("gmail.create_draft")
        assert result["risk_level"] == RiskLevel.MEDIUM
        assert result["requires_approval"] is False

    def test_high_risk_send(self):
        result = self.evaluator.evaluate("gmail.send_email", {"to": ["a@b.com"]})
        assert result["risk_level"] == RiskLevel.HIGH
        assert result["requires_approval"] is True

    def test_high_risk_delete(self):
        result = self.evaluator.evaluate("calendar.delete_event")
        assert result["risk_level"] == RiskLevel.HIGH
        assert result["requires_approval"] is True

    def test_high_risk_share(self):
        result = self.evaluator.evaluate("drive.share_file")
        assert result["risk_level"] == RiskLevel.HIGH
        assert result["requires_approval"] is True

    def test_low_risk_calendar_read(self):
        result = self.evaluator.evaluate("calendar.search_events")
        assert result["risk_level"] == RiskLevel.LOW

    def test_batch_evaluation(self):
        steps = [
            {"step": 1, "tool": "gmail.search", "args": {}},
            {"step": 2, "tool": "gmail.send_email", "args": {"to": ["test@test.com"]}},
        ]
        results = self.evaluator.evaluate_batch(steps)
        assert len(results) == 2
        assert results[0]["risk_level"] == RiskLevel.LOW
        assert results[1]["risk_level"] == RiskLevel.HIGH
