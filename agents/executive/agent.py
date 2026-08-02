"""
Executive Agent — the CEO of Animus Studio.

Responsibilities:
- Read the mission and determine which workflow to run
- Coordinate agents in the correct sequence
- Gate-keep human approval steps
- Handle failures and retries
- Never create content directly

Org chart:
Executive Agent
├── Research Department
├── Creative Department  (Script + Review)
├── Media Department     (Voice + Editor + Thumbnail)
├── Publishing Department
└── Analytics Department
"""
from __future__ import annotations
from typing import Any

from agents.base import BaseAgent, AgentContext


WORKFLOW_STEPS = {
    "daily_content": [
        "research",
        "script",
        "review",
        "voice",
        "editor",
        "thumbnail",
        "publisher",
        "analytics",
    ],
    "breaking_news": ["research", "review", "script", "publisher"],
    "weekly_review": ["analytics"],
}


class ExecutiveAgent(BaseAgent):
    name = "executive"
    department = "executive"

    async def _run(self, context: AgentContext, input_data: dict[str, Any]) -> dict[str, Any]:
        workflow = input_data.get("workflow", "daily_content")
        mission = input_data.get("mission", {})
        requires_approval = mission.get("requires_approval", True)

        self._log.info("executive.planning", workflow=workflow, mission_id=context.mission_id)

        steps = WORKFLOW_STEPS.get(workflow, WORKFLOW_STEPS["daily_content"])

        plan = {
            "workflow": workflow,
            "steps": steps,
            "mission": mission,
            "requires_approval": requires_approval,
            "status": "planned",
        }

        # Use LLM to refine the plan based on mission goal
        refined = await self.llm_json([
            {
                "role": "system",
                "content": (
                    "You are the Executive Agent of Animus Studio, an autonomous media OS. "
                    "Your job is to plan the optimal workflow execution for a given mission. "
                    "Return a JSON object with: steps (list), priority_focus (string), "
                    "estimated_duration_minutes (int), notes (string)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Mission goal: {mission.get('goal', 'Grow the channel')}\n"
                    f"Workflow: {workflow}\n"
                    f"Brand tone: {context.brand.get('tone', 'professional')}\n"
                    f"Target audience: {context.brand.get('target_audience', 'general')}\n"
                    f"Steps: {steps}"
                ),
            },
        ])

        plan.update(refined)
        context.set("executive_plan", plan)

        self._log.info("executive.plan_ready", steps=steps)
        return plan
