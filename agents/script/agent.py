"""
Script Agent — Department: Creative

Input: Research brief
Output: Full script with title, hook, body, CTA, description, tags
"""
from __future__ import annotations
from typing import Any

from agents.base import BaseAgent, AgentContext

SCRIPT_SYSTEM_PROMPT = """You are the Script Agent for Animus Studio.
You write compelling video scripts tailored to the creator's voice and brand.

Return JSON with:
{
  "title": "...",
  "hook": "First 3-5 seconds — must stop the scroll",
  "script": "Full narration script with [PAUSE] and [EMPHASIS] markers",
  "sections": [{"heading": "...", "content": "..."}],
  "cta": "Call to action at the end",
  "description": "YouTube/platform description",
  "tags": ["tag1", "tag2"],
  "estimated_duration_seconds": 60,
  "word_count": 150
}"""


class ScriptAgent(BaseAgent):
    name = "script"
    department = "creative"

    async def _run(self, context: AgentContext, input_data: dict[str, Any]) -> dict[str, Any]:
        research = context.get("research_brief", input_data.get("research_brief", {}))
        brand = context.brand
        mission = input_data.get("mission", {})

        self._log.info("script.writing", topic=research.get("topic"))

        script = await self.llm_json(
            context,
            [
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Topic: {research.get('topic')}\n"
                    f"Angle: {research.get('angle')}\n"
                    f"Audience: {research.get('audience')}\n"
                    f"Brand tone: {brand.get('tone', 'professional')}\n"
                    f"Style: {mission.get('style', 'informative')}\n"
                    f"Content type: {research.get('content_type', 'short')}\n"
                    f"Keywords: {research.get('keywords', [])}\n\n"
                    "Write the full video script."
                ),
            },
        ])

        self._log.info("script.complete", title=script.get("title"), words=script.get("word_count"))
        context.set("script", script)
        return script
