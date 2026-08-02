"""
Research Agent — Department: Research

Capabilities required:
  - TEXT_REASONING (LLM synthesis)
  - WEB_SEARCH (web search)

Uses ResearchEngine to gather multi-source material,
then synthesizes a research brief via the LLM.

Also checks memory for past topics to avoid duplication.
"""
from __future__ import annotations
from typing import Any

from agents.base import BaseAgent
from runtime.capabilities import Capability

RESEARCH_SYSTEM_PROMPT = """You are a Research Director for an autonomous media company.

Your job: find the most compelling, fresh, and relevant topic for a video
given the brand's mission and past performance.

Return JSON:
{
  "topic": "...",
  "summary": "2-3 sentence summary of what the video will cover",
  "key_points": ["...", "..."],
  "suggested_angle": "unique perspective or framing",
  "hook_idea": "attention-grabbing opening concept",
  "trending_score": 0.0-1.0,
  "risk_score": 0.0-1.0
}"""


class ResearchAgent(BaseAgent):
    name       = "research"
    department = "research"
    requires   = {Capability.TEXT_REASONING, Capability.WEB_SEARCH}
    produces   = {"research_brief"}

    async def _run(self, rt_or_ctx: Any, spec_or_input: Any, exec_or_none: Any = None) -> dict[str, Any]:
        # Handle both (rt, spec, exec) and (context, input_data)
        if exec_or_none is not None:
            spec = spec_or_input
            goal = spec.goal
            brand_name = spec.brand_name
            audience = spec.audience
            tone = spec.tone
            provider = rt_or_ctx.runtime
            db_session = getattr(spec, "db", None)
            brand_id = spec.brand_id
        else:
            context = rt_or_ctx
            input_data = spec_or_input
            mission = input_data.get("mission", {})
            goal = mission.get("goal", "")
            brand = context.brand or {}
            brand_name = brand.get("name", "Unknown")
            audience = brand.get("target_audience", "general")
            tone = brand.get("tone", "professional")
            provider = context.provider
            db_session = input_data.get("db")
            brand_id = brand.get("id")

        self._log.info("research.starting", goal=goal)

        # ── Memory recall — avoid duplicating past topics ──────
        memory_context = ""
        if db_session and brand_id:
            try:
                from knowledge.memory import memory as mem_engine
                from knowledge.types import MemoryType
                memory_context = await mem_engine.recall_for_prompt(
                    db=db_session,
                    query=goal,
                    brand_id=brand_id,
                    memory_types=[MemoryType.VIDEO, MemoryType.AUDIENCE, MemoryType.PLATFORM],
                    top_k=3,
                )
            except Exception as exc:
                self._log.warning("research.memory_skip", error=str(exc))

        # ── Multi-source research via ResearchEngine ───────────
        from research.engine import research_engine
        brief = await research_engine.research(
            query=goal,
            brand={"name": brand_name, "target_audience": audience, "tone": tone},
            provider=provider,
        )

        # ── LLM synthesis with full context ───────────────────
        result = await self.llm_json(
            rt_or_ctx,
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Mission: {goal}\n"
                        f"Brand: {brand_name}\n"
                        f"Audience: {audience}\n"
                        f"Tone: {tone}\n\n"
                        + (f"=== PAST TOPICS (avoid duplicating) ===\n{memory_context}\n\n" if memory_context else "")
                        + f"=== RESEARCH GATHERED ===\n{brief.raw_context}\n\n"
                        "Choose the most compelling FRESH angle. Return the JSON brief."
                    ),
                },
            ],
            capability=Capability.TEXT_REASONING,
        )

        result["sources"] = brief.sources
        result["confidence"] = brief.confidence
        self._log.info("research.done", topic=result.get("topic"), risk=result.get("risk_score"))

        if hasattr(rt_or_ctx, "set"):
            rt_or_ctx.set("research_brief", result)

        return {"research_brief": result}
