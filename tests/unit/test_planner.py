"""Unit tests for the planner."""

from __future__ import annotations

from agent.planner import Planner


class TestPlanner:
    def setup_method(self):
        self.planner = Planner()

    def test_mock_plan_email(self):
        plan = self.planner.create_plan("Send an email to the team")
        assert plan.task_id.startswith("tsk_")
        assert len(plan.steps) > 0
        # Should involve gmail tools
        tools = [s.tool for s in plan.steps]
        assert any("gmail" in t for t in tools)

    def test_mock_plan_calendar(self):
        plan = self.planner.create_plan("Create a meeting tomorrow")
        assert len(plan.steps) > 0
        tools = [s.tool for s in plan.steps]
        assert any("calendar" in t for t in tools)

    def test_mock_plan_sheets(self):
        plan = self.planner.create_plan("Read the spreadsheet data")
        assert len(plan.steps) > 0
        tools = [s.tool for s in plan.steps]
        assert any("sheets" in t for t in tools)

    def test_mock_plan_drive(self):
        plan = self.planner.create_plan("Find files in my drive")
        assert len(plan.steps) > 0
        tools = [s.tool for s in plan.steps]
        assert any("drive" in t for t in tools)

    def test_plan_has_intent(self):
        plan = self.planner.create_plan("Write a document")
        assert plan.intent != ""
