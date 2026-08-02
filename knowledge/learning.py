"""
Learning System — writes outcomes back into memory after each publish cycle.

After a video publishes and analytics are collected:
  1. Build a VIDEO memory entry from the script + analytics
  2. Update AUDIENCE memory with engagement signals
  3. Update PLATFORM memory with timing/format lessons
  4. Generate STRATEGY insights for the brand's next cycle

This is the feedback loop that makes Animus Studio smarter over time.
"""
from __future__ import annotations
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.types import (
    MemoryEntry, MemoryType,
    VIDEO_MEMORY_TEMPLATE, AUDIENCE_MEMORY_TEMPLATE, PLATFORM_MEMORY_TEMPLATE,
)
from knowledge.memory import memory
import litellm

logger = structlog.get_logger()


class LearningEngine:

    async def learn_from_video(
        self,
        db: AsyncSession,
        brand_id: str,
        video: dict[str, Any],
        analytics: dict[str, Any],
    ) -> None:
        """
        Called after analytics are fetched for a published video.
        Writes structured learnings to all relevant memory layers.
        """
        logger.info("learning.started", brand_id=brand_id, video_id=video.get("id"))

        # ── 1. Video Memory ──────────────────────────────────
        await self._learn_video(db, brand_id, video, analytics)

        # ── 2. Audience Memory ───────────────────────────────
        await self._learn_audience(db, brand_id, video, analytics)

        # ── 3. Platform Memory ───────────────────────────────
        await self._learn_platform(db, brand_id, video, analytics)

        logger.info("learning.complete", brand_id=brand_id, video_id=video.get("id"))

    async def _learn_video(
        self,
        db: AsyncSession,
        brand_id: str,
        video: dict,
        analytics: dict,
    ) -> None:
        ctr = analytics.get("ctr", 0)
        views = analytics.get("views", 0)
        retention = analytics.get("retention_rate", 0)

        # Determine outcome label
        if ctr >= 5 and retention >= 50:
            outcome = "strong_hit"
        elif ctr >= 3 or retention >= 40:
            outcome = "average"
        else:
            outcome = "underperformer"

        # Use LLM to extract the lesson
        lesson = await self._extract_lesson(video, analytics, outcome)

        content = VIDEO_MEMORY_TEMPLATE.format(
            title=video.get("title", "Unknown"),
            hook=video.get("hook", ""),
            outcome=outcome,
            views=views,
            ctr=round(ctr, 2),
            retention=round(retention, 1),
            worked=lesson.get("worked", ""),
            failed=lesson.get("failed", ""),
            lesson=lesson.get("lesson", ""),
        )

        entry = MemoryEntry(
            brand_id=brand_id,
            type=MemoryType.VIDEO,
            title=f"Video: {video.get('title', 'Unknown')} ({outcome})",
            content=content,
            metadata={
                "video_id": video.get("id"),
                "outcome": outcome,
                "ctr": ctr,
                "views": views,
            },
        )
        await memory.store(db, entry)

    async def _learn_audience(
        self,
        db: AsyncSession,
        brand_id: str,
        video: dict,
        analytics: dict,
    ) -> None:
        platform = video.get("platform", "youtube")
        top_comments = analytics.get("top_comments", [])

        content = AUDIENCE_MEMORY_TEMPLATE.format(
            platform=platform,
            observation=f"Video '{video.get('title')}' got {analytics.get('views', 0)} views",
            engagement_signal=(
                f"CTR {analytics.get('ctr', 0):.1f}%, "
                f"retention {analytics.get('retention_rate', 0):.1f}%"
            ),
            top_comments="; ".join(top_comments[:3]) if top_comments else "N/A",
            preferred_topics=video.get("topic", ""),
            avoid="",
        )

        entry = MemoryEntry(
            brand_id=brand_id,
            type=MemoryType.AUDIENCE,
            title=f"Audience signal: {platform} — {video.get('title', '')}",
            content=content,
            metadata={"platform": platform, "video_id": video.get("id")},
        )
        await memory.store(db, entry)

    async def _learn_platform(
        self,
        db: AsyncSession,
        brand_id: str,
        video: dict,
        analytics: dict,
    ) -> None:
        platform = video.get("platform", "youtube")
        published_at = video.get("published_at", "")

        content = PLATFORM_MEMORY_TEMPLATE.format(
            platform=platform,
            best_times=published_at,
            optimal_length=f"{video.get('duration_seconds', 60)}s",
            thumbnail_style="",
            caption_style="",
            hashtag_strategy="",
        )

        entry = MemoryEntry(
            brand_id=brand_id,
            type=MemoryType.PLATFORM,
            title=f"Platform lesson: {platform}",
            content=content,
            metadata={"platform": platform},
        )
        await memory.store(db, entry)

    async def _extract_lesson(
        self,
        video: dict,
        analytics: dict,
        outcome: str,
    ) -> dict[str, str]:
        """Ask LLM to identify what worked/failed from the video + analytics data."""
        response = await litellm.acompletion(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an analytics expert for a YouTube content creator. "
                        "Given a video's metadata and performance, extract what worked, "
                        "what failed, and a single key lesson. "
                        "Return JSON: {worked: str, failed: str, lesson: str}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Title: {video.get('title')}\n"
                        f"Hook: {video.get('hook')}\n"
                        f"Script excerpt: {str(video.get('script', ''))[:500]}\n"
                        f"Outcome: {outcome}\n"
                        f"Views: {analytics.get('views')}\n"
                        f"CTR: {analytics.get('ctr')}%\n"
                        f"Retention: {analytics.get('retention_rate')}%\n"
                        f"Likes: {analytics.get('likes')}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(response.choices[0].message.content)


# ─── Singleton ────────────────────────────────────────────────
learning = LearningEngine()
