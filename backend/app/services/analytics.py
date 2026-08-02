"""
Analytics Service — fetches and persists platform metrics.

Currently implemented: YouTube Analytics API (via google-api-python-client)
Stub: Instagram, LinkedIn, X

After fetching, metrics are:
  1. Persisted to the `analytics` table
  2. Passed to the LearningEngine to update memory
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AnalyticsService:

    async def fetch_and_store(
        self,
        db: AsyncSession,
        video_id: str,
        platform: str,
        platform_video_id: str,
        access_token: str,
    ) -> dict[str, Any]:
        """
        Fetch metrics for a video from the given platform,
        persist to DB, and return the raw metrics dict.
        """
        if platform == "youtube":
            metrics = await self._fetch_youtube(platform_video_id, access_token)
        else:
            logger.warning("analytics.unsupported_platform", platform=platform)
            metrics = {}

        if metrics:
            await self._persist(db, video_id, platform, metrics)

        return metrics

    async def _fetch_youtube(
        self,
        video_id: str,
        access_token: str,
    ) -> dict[str, Any]:
        """
        YouTube Data API v3 + YouTube Analytics API.
        Fetches views, likes, comments, CTR, avgViewDuration, estimatedRevenue.
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        # ── Video stats (Data API) ─────────────────────────
        stats_url = (
            f"https://www.googleapis.com/youtube/v3/videos"
            f"?part=statistics&id={video_id}"
        )
        # ── Analytics (Analytics API) ──────────────────────
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        analytics_url = (
            "https://youtubeanalytics.googleapis.com/v2/reports"
            f"?ids=channel==MINE"
            f"&filters=video=={video_id}"
            f"&startDate=2020-01-01&endDate={today}"
            f"&metrics=views,likes,comments,shares,estimatedMinutesWatched,"
            f"averageViewDuration,averageViewPercentage,annotationClickThroughRate"
        )

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                stats_resp = await client.get(stats_url, headers=headers)
                stats_resp.raise_for_status()
                stats_data = stats_resp.json()

                analytics_resp = await client.get(analytics_url, headers=headers)
                analytics_resp.raise_for_status()
                analytics_data = analytics_resp.json()
            except httpx.HTTPError as e:
                logger.error("analytics.youtube.fetch_failed", video_id=video_id, error=str(e))
                return {}

        # Parse stats
        items = stats_data.get("items", [{}])
        stats = items[0].get("statistics", {}) if items else {}

        # Parse analytics rows
        rows = analytics_data.get("rows", [[]])
        row = rows[0] if rows else []
        col_headers = [c["name"] for c in analytics_data.get("columnHeaders", [])]

        def col(name: str) -> float:
            idx = col_headers.index(name) if name in col_headers else -1
            return float(row[idx]) if idx >= 0 and idx < len(row) else 0.0

        return {
            "views":            int(stats.get("viewCount", 0)),
            "likes":            int(stats.get("likeCount", 0)),
            "comments":         int(stats.get("commentCount", 0)),
            "shares":           col("shares"),
            "avg_view_duration": col("averageViewDuration"),
            "retention_rate":   col("averageViewPercentage"),
            "ctr":              col("annotationClickThroughRate"),
            "estimated_minutes": col("estimatedMinutesWatched"),
            "revenue":          0.0,   # requires monetization API
            "rpm":              0.0,
        }

    async def _persist(
        self,
        db: AsyncSession,
        video_id: str,
        platform: str,
        metrics: dict[str, Any],
    ) -> None:
        import json
        await db.execute(
            text("""
                INSERT INTO analytics
                    (id, video_id, platform, views, likes, comments, shares,
                     ctr, avg_view_duration, retention_rate, revenue, rpm, raw_data)
                VALUES
                    (:id, :video_id, :platform, :views, :likes, :comments, :shares,
                     :ctr, :avg_view_duration, :retention_rate, :revenue, :rpm, :raw_data)
            """),
            {
                "id": str(uuid.uuid4()),
                "video_id": video_id,
                "platform": platform,
                "views": metrics.get("views", 0),
                "likes": metrics.get("likes", 0),
                "comments": metrics.get("comments", 0),
                "shares": metrics.get("shares", 0),
                "ctr": metrics.get("ctr", 0),
                "avg_view_duration": metrics.get("avg_view_duration", 0),
                "retention_rate": metrics.get("retention_rate", 0),
                "revenue": metrics.get("revenue", 0),
                "rpm": metrics.get("rpm", 0),
                "raw_data": json.dumps(metrics),
            },
        )
        logger.info("analytics.persisted", video_id=video_id, platform=platform, views=metrics.get("views"))


analytics_service = AnalyticsService()
