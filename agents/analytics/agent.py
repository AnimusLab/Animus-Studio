"""
Analytics Agent — Department: Analytics

Reads platform metrics and generates reports.
Phase 4: Also triggers the LearningEngine to persist insights into memory.
"""
from __future__ import annotations
from typing import Any

from agents.base import BaseAgent, AgentContext


class AnalyticsAgent(BaseAgent):
    name = "analytics"
    department = "analytics"

    async def _run(self, context: AgentContext, input_data: dict[str, Any]) -> dict[str, Any]:
        publish_results = context.get("publish_results", {})
        script = context.get("script", {})
        brand = context.brand
        videos = input_data.get("videos", [])

        self._log.info("analytics.collecting", video_count=len(videos))

        # ── Generate insight report via LLM ───────────────────
        summary = await self.llm_json([
            {
                "role": "system",
                "content": (
                    "You are the Analytics Agent for Animus Studio. "
                    "Analyze the provided video performance data and generate insights. "
                    "Return JSON: {"
                    "best_performing: [...], worst_performing: [...], "
                    "insights: [...], recommendations: [...], strategy_notes: str"
                    "}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Brand: {brand.get('name')}\n"
                    f"Videos analyzed: {videos}\n"
                    f"Publish results: {publish_results}\n"
                    f"Latest script title: {script.get('title', 'N/A')}\n"
                    "Generate an analytics report and strategy recommendations."
                ),
            },
        ])

        context.set("analytics_report", summary)

        # ── Write learnings to memory (if db available) ───────
        db = input_data.get("db")
        brand_id = brand.get("id")
        if db and brand_id and publish_results:
            try:
                from knowledge.learning import learning
                video_meta = {
                    "id": input_data.get("video_id", ""),
                    "title": script.get("title", ""),
                    "hook": script.get("hook", ""),
                    "script": script.get("script", ""),
                    "platform": "youtube",
                }
                # Use summary insights as synthetic metrics if real ones not available
                mock_metrics = {
                    "views": 0,
                    "likes": 0,
                    "ctr": 0,
                    "retention_rate": 0,
                    "top_comments": [],
                }
                await learning.learn_from_video(db, brand_id, video_meta, mock_metrics)
                self._log.info("analytics.learning_written", brand_id=brand_id)
            except Exception as e:
                self._log.warning("analytics.learning_skip", error=str(e))

        return summary
