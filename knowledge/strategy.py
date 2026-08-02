"""
Strategy Engine — weekly intelligence report for a brand.

Reads all memory layers, analyzes performance patterns,
and generates a concrete strategy recommendation for the next content cycle.

Output:
  - Best performing topics/formats
  - Worst performing content to avoid
  - Specific action items for next week
  - Suggested titles for next 3 videos
"""
from __future__ import annotations
from typing import Any
import json

import structlog
import litellm
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.types import MemoryType
from knowledge.memory import memory

logger = structlog.get_logger()

STRATEGY_SYSTEM_PROMPT = """You are the Strategy Director for an autonomous media company.

Given a brand's memory bank (past video performance, audience signals, platform lessons),
generate a concrete weekly strategy report.

Return JSON:
{
  "summary": "1-2 sentence overview",
  "top_performing_topics": ["topic1", "topic2"],
  "avoid": ["topic or format to avoid"],
  "format_recommendations": ["short-form beats long-form this week", ...],
  "suggested_titles": ["Title 1", "Title 2", "Title 3"],
  "action_items": ["Post at 9am EST based on platform data", ...],
  "confidence": 0.0-1.0
}"""


class StrategyEngine:

    async def generate_weekly_report(
        self,
        db: AsyncSession,
        brand_id: str,
        brand: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Pull all memory for a brand and generate a strategy report.
        """
        logger.info("strategy.generating", brand_id=brand_id)

        # Pull memories across all relevant types
        video_memories  = await memory.list_by_type(db, brand_id, MemoryType.VIDEO, limit=20)
        audience_mem    = await memory.list_by_type(db, brand_id, MemoryType.AUDIENCE, limit=10)
        platform_mem    = await memory.list_by_type(db, brand_id, MemoryType.PLATFORM, limit=10)
        brand_mem       = await memory.list_by_type(db, brand_id, MemoryType.BRAND, limit=5)

        # Format for prompt
        video_context = "\n---\n".join(m.content for m in video_memories)
        audience_context = "\n---\n".join(m.content for m in audience_mem)
        platform_context = "\n---\n".join(m.content for m in platform_mem)
        brand_context = "\n---\n".join(m.content for m in brand_mem)

        response = await litellm.acompletion(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": STRATEGY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Brand: {brand.get('name')}\n"
                        f"Goal: {brand.get('goal', 'Grow the channel')}\n"
                        f"Target audience: {brand.get('target_audience')}\n\n"
                        f"=== BRAND MEMORY ===\n{brand_context or 'None yet'}\n\n"
                        f"=== PAST VIDEO PERFORMANCE ===\n{video_context or 'No videos yet'}\n\n"
                        f"=== AUDIENCE SIGNALS ===\n{audience_context or 'None yet'}\n\n"
                        f"=== PLATFORM LESSONS ===\n{platform_context or 'None yet'}\n\n"
                        "Generate the weekly strategy report."
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )

        report = json.loads(response.choices[0].message.content)
        logger.info("strategy.complete", brand_id=brand_id, confidence=report.get("confidence"))
        return report


# ─── Singleton ────────────────────────────────────────────────
strategy = StrategyEngine()
