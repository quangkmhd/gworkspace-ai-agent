"""Agent planner — LLM-based planner that takes user prompt → produces structured TaskPlan.

Uses LangChain ChatModels (configurable: Gemini, OpenAI, Anthropic) to generate
structured plans mapping to tools.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from agent.prompts import DEVELOPER_PROMPT, PLANNER_PROMPT, SYSTEM_PROMPT
from agent.schemas import PlanStep, TaskPlan
from backend.config import get_settings
from backend.schemas.common import generate_task_id

logger = structlog.get_logger("planner")


def _get_llm() -> Any:
    """Build the configured LLM instance."""
    settings = get_settings()

    if settings.MOCK_MODE:
        return None  # Mock mode doesn't need LLM

    provider = settings.LLM_PROVIDER.lower()

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_TOKENS,
        )
    elif provider == "vertex":
        from langchain_google_vertexai import ChatVertexAI

        return ChatVertexAI(
            model_name=settings.LLM_MODEL,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_TOKENS,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _parse_plan_response(response_text: str) -> dict[str, Any]:
    """Parse LLM response to extract plan JSON."""
    text = response_text.strip()
    # Try to find JSON block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("plan_parse_failed", response=response_text[:200])
        return {"intent": "unknown", "steps": []}


class Planner:
    """LLM-based task planner."""

    def __init__(self) -> None:
        self._llm = _get_llm()

    def create_plan(
        self,
        user_input: str,
        user_id: str = "anonymous",
        locale: str = "en",
        context: dict[str, Any] | None = None,
    ) -> TaskPlan:
        """Generate a structured task plan from user input."""
        settings = get_settings()

        if settings.MOCK_MODE:
            return self._mock_plan(user_input)

        from langchain_core.messages import HumanMessage, SystemMessage

        prompt = PLANNER_PROMPT.format(
            user_input=user_input,
            user_id=user_id,
            locale=locale,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + DEVELOPER_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = self._llm.invoke(messages)
        plan_data = _parse_plan_response(response.content)

        task_id = generate_task_id()
        steps = [
            PlanStep(
                step=s.get("step", i + 1),
                goal=s.get("goal", ""),
                tool=s.get("tool", ""),
                args=s.get("args", {}),
                depends_on=s.get("depends_on", []),
            )
            for i, s in enumerate(plan_data.get("steps", []))
        ]

        plan = TaskPlan(
            task_id=task_id,
            intent=plan_data.get("intent", ""),
            steps=steps,
        )

        logger.info("plan_created", task_id=task_id, steps=len(steps))
        return plan

    def _mock_plan(self, user_input: str) -> TaskPlan:
        """Generate a mock plan for testing."""
        prompt_lower = user_input.lower()
        steps: list[PlanStep] = []

        if "email" in prompt_lower or "mail" in prompt_lower:
            steps = [
                PlanStep(step=1, goal="Search for relevant emails", tool="gmail.search", args={"query": user_input}),
                PlanStep(step=2, goal="Create draft email", tool="gmail.create_draft", args={"to": ["user@example.com"], "subject": "Response", "body": "Auto-generated draft"}, depends_on=[1]),
            ]
        elif "calendar" in prompt_lower or "event" in prompt_lower or "meeting" in prompt_lower:
            steps = [
                PlanStep(step=1, goal="Get current datetime", tool="calendar.get_current_datetime", args={"timezone": "Asia/Ho_Chi_Minh"}),
                PlanStep(step=2, goal="Search existing events", tool="calendar.search_events", args={"calendar_id": "primary", "time_min": "2024-01-15T00:00:00Z", "time_max": "2024-01-15T23:59:59Z"}, depends_on=[1]),
            ]
        elif "sheet" in prompt_lower or "spreadsheet" in prompt_lower:
            steps = [
                PlanStep(step=1, goal="Read sheet data", tool="sheets.read_data", args={"spreadsheet_id": "example_id", "range": "Sheet1!A1:Z100"}),
            ]
        elif "doc" in prompt_lower or "document" in prompt_lower:
            steps = [
                PlanStep(step=1, goal="Create a new document", tool="docs.create_document", args={"title": "New Document"}),
            ]
        elif "drive" in prompt_lower or "file" in prompt_lower:
            steps = [
                PlanStep(step=1, goal="Search files in Drive", tool="drive.search_files", args={"query": user_input}),
            ]
        else:
            steps = [
                PlanStep(step=1, goal="Search emails about the topic", tool="gmail.search", args={"query": user_input}),
            ]

        return TaskPlan(
            task_id=generate_task_id(),
            intent=f"Handle request: {user_input[:50]}",
            steps=steps,
        )
