"""Agent executor — LangGraph StateGraph with interrupt for HITL.

Implements the agent execution loop:
  plan_node → evaluate_risk → execute_or_interrupt → aggregate_results
"""

from __future__ import annotations

import time
from typing import Any, TypedDict

import structlog

from agent.risk_evaluator import RiskEvaluator
from agent.schemas import ActionProposal, AgentState, TaskPlan
from backend.config import get_settings
from backend.schemas.common import ActionStatus, TaskStatus, generate_action_id
from tools.registry import ToolRegistry

logger = structlog.get_logger("executor")


class GraphState(TypedDict, total=False):
    """LangGraph state dict for the agent workflow."""

    task_id: str
    user_id: str
    prompt: str
    status: str
    plan: dict[str, Any] | None
    actions: list[dict[str, Any]]
    current_step: int
    results: list[dict[str, Any]]
    error: str | None
    pending_approvals: list[dict[str, Any]]


class AgentExecutor:
    """Executes agent plans with risk evaluation and HITL gates.

    Uses LangGraph's interrupt() pattern for high-risk actions.
    When not using the full LangGraph graph (e.g., in mock mode or simple
    execution), this class provides a step-by-step executor.
    """

    def __init__(self) -> None:
        self._registry = ToolRegistry.get()
        self._risk_evaluator = RiskEvaluator()
        self._settings = get_settings()

    def execute_plan(self, state: AgentState) -> AgentState:
        """Execute an agent plan step-by-step.

        For each step:
          1. Evaluate risk
          2. If high-risk → mark as pending_approval
          3. If auto-executable → execute and store result
        """
        if not state.plan or not state.plan.steps:
            state.status = TaskStatus.FAILED
            state.error = "No plan to execute"
            return state

        state.status = TaskStatus.EXECUTING
        pending_approvals: list[ActionProposal] = []

        for plan_step in state.plan.steps:
            # Check dependencies
            deps_met = all(
                any(
                    a.step == dep and a.status == ActionStatus.COMPLETED
                    for a in state.actions
                )
                for dep in plan_step.depends_on
            )
            if not deps_met and plan_step.depends_on:
                # Skip if dependencies not met (might be waiting approval)
                continue

            # Evaluate risk
            risk = self._risk_evaluator.evaluate(plan_step.tool, plan_step.args)
            action = ActionProposal(
                action_id=generate_action_id(),
                step=plan_step.step,
                tool=plan_step.tool,
                args=plan_step.args,
                risk_level=risk["risk_level"],
                requires_approval=risk["requires_approval"],
                reason=risk["reason"],
            )

            if risk["requires_approval"]:
                action.status = ActionStatus.PENDING_APPROVAL
                pending_approvals.append(action)
                state.actions.append(action)
                logger.info(
                    "action_pending_approval",
                    action_id=action.action_id,
                    tool=action.tool,
                )
                continue

            # Auto-execute
            try:
                action.status = ActionStatus.EXECUTING
                result = self._registry.invoke(plan_step.tool, plan_step.args)
                action.status = ActionStatus.COMPLETED
                action.result = result
                state.results.append({
                    "step": plan_step.step,
                    "tool": plan_step.tool,
                    "result": result,
                })
                logger.info("action_completed", action_id=action.action_id, tool=action.tool)
            except Exception as e:
                action.status = ActionStatus.FAILED
                action.error = str(e)
                logger.error("action_failed", action_id=action.action_id, error=str(e))

            state.actions.append(action)

        # Determine final status
        if pending_approvals:
            state.status = TaskStatus.WAITING_APPROVAL
        elif any(a.status == ActionStatus.FAILED for a in state.actions):
            state.status = TaskStatus.FAILED
            failed = [a for a in state.actions if a.status == ActionStatus.FAILED]
            state.error = f"{len(failed)} action(s) failed"
        else:
            state.status = TaskStatus.COMPLETED

        return state

    def resume_after_approval(
        self,
        state: AgentState,
        approved_action_ids: list[str],
        edited_args: dict[str, dict[str, Any]] | None = None,
    ) -> AgentState:
        """Resume execution after HITL approval.

        Args:
            state: Current agent state
            approved_action_ids: IDs of approved actions
            edited_args: Optional edited args keyed by action_id
        """
        for action in state.actions:
            if action.action_id not in approved_action_ids:
                continue
            if action.status != ActionStatus.PENDING_APPROVAL:
                continue

            # Use edited args if provided
            args = action.args
            if edited_args and action.action_id in edited_args:
                args = edited_args[action.action_id]
                action.args = args

            action.status = ActionStatus.APPROVED
            try:
                result = self._registry.invoke(action.tool, args)
                action.status = ActionStatus.COMPLETED
                action.result = result
                state.results.append({
                    "step": action.step,
                    "tool": action.tool,
                    "result": result,
                })
            except Exception as e:
                action.status = ActionStatus.FAILED
                action.error = str(e)

        # Re-evaluate status
        pending = [a for a in state.actions if a.status == ActionStatus.PENDING_APPROVAL]
        if pending:
            state.status = TaskStatus.WAITING_APPROVAL
        elif any(a.status == ActionStatus.FAILED for a in state.actions):
            state.status = TaskStatus.FAILED
        else:
            state.status = TaskStatus.COMPLETED

        return state

    def build_langgraph(self) -> Any:
        """Build a LangGraph StateGraph for full agent execution.

        This creates the graph with interrupt support for HITL.
        Uses:
          - langgraph.graph.StateGraph
          - langgraph.types.interrupt
          - langgraph.checkpoint.sqlite.SqliteSaver (or MemorySaver)
        """
        try:
            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.graph import END, StateGraph
            from langgraph.types import Command, interrupt
        except ImportError:
            logger.warning("langgraph_not_available", msg="LangGraph not installed, using simple executor")
            return None

        def plan_node(state: GraphState) -> GraphState:
            """Planning node — uses LLM to create plan."""
            from agent.planner import Planner

            planner = Planner()
            plan = planner.create_plan(
                user_input=state.get("prompt", ""),
                user_id=state.get("user_id", ""),
            )
            state["plan"] = plan.model_dump()
            state["status"] = TaskStatus.PLANNING.value
            return state

        def risk_node(state: GraphState) -> GraphState:
            """Risk evaluation node."""
            plan = state.get("plan")
            if not plan or not plan.get("steps"):
                state["error"] = "No plan to evaluate"
                return state

            actions = []
            for step in plan["steps"]:
                risk = self._risk_evaluator.evaluate(step["tool"], step.get("args", {}))
                actions.append({
                    "action_id": generate_action_id(),
                    "step": step["step"],
                    "tool": step["tool"],
                    "args": step.get("args", {}),
                    "risk_level": risk["risk_level"].value,
                    "requires_approval": risk["requires_approval"],
                    "reason": risk["reason"],
                    "status": "planned",
                })
            state["actions"] = actions
            return state

        def execute_node(state: GraphState) -> GraphState:
            """Execution node with interrupt for HITL."""
            actions = state.get("actions", [])
            results = state.get("results", [])
            pending = []

            for action in actions:
                if action["status"] != "planned":
                    continue

                if action["requires_approval"]:
                    # Interrupt for approval
                    action["status"] = "pending_approval"
                    pending.append(action)
                    approval = interrupt({
                        "type": "approval_request",
                        "action": action,
                        "message": f"Approve {action['tool']}? {action['reason']}",
                    })
                    if approval.get("approved"):
                        action["args"] = approval.get("edited_args", action["args"])
                        action["status"] = "approved"
                    else:
                        action["status"] = "rejected"
                        continue

                # Execute
                try:
                    result = self._registry.invoke(action["tool"], action["args"])
                    action["status"] = "completed"
                    action["result"] = result
                    results.append({"step": action["step"], "tool": action["tool"], "result": result})
                except Exception as e:
                    action["status"] = "failed"
                    action["error"] = str(e)

            state["actions"] = actions
            state["results"] = results
            state["pending_approvals"] = pending

            if pending:
                state["status"] = "waiting_approval"
            elif any(a["status"] == "failed" for a in actions):
                state["status"] = "failed"
            else:
                state["status"] = "completed"

            return state

        # Build graph
        graph = StateGraph(GraphState)
        graph.add_node("plan", plan_node)
        graph.add_node("evaluate_risk", risk_node)
        graph.add_node("execute", execute_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "evaluate_risk")
        graph.add_edge("evaluate_risk", "execute")
        graph.add_edge("execute", END)

        checkpointer = MemorySaver()
        compiled = graph.compile(checkpointer=checkpointer)
        return compiled
