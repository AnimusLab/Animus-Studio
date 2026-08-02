"""
Research Engine

Orchestrates multi-source research for a given topic/query.

Source priority:
  0. Memory recall (check if previously researched)
  1. YouTube trending (no key, public RSS)
  2. DuckDuckGo / configured search provider
  3. Wikipedia REST API
  4. RSS feeds
  5. Direct web scrape (Playwright, rate-limited)
  6. LLM synthesis of all gathered material

Output: ResearchBrief
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import structlog
from runtime.capabilities import Capability

logger = structlog.get_logger()


@dataclass
class ResearchBrief:
    topic: str
    summary: str
    key_points: list[str]
    suggested_angle: str
    sources: list[dict[str, str]] = field(default_factory=list)
    trending_score: float = 0.0
    confidence: float = 0.85
    raw_context: str = ""


class ResearchEngine:
    """
    Multi-source research engine.
    Workers call engine.research(query, brand) — never raw search APIs directly.
    """

    async def research(
        self,
        query: str,
        brand: dict[str, Any] | None = None,
        provider: Any | None = None,    # CapabilityRegistry or Runtime, injected by worker
    ) -> ResearchBrief:
        brand = brand or {}
        logger.info("research.starting", query=query)

        # ── Gather raw material from all sources in parallel ──
        results = await asyncio.gather(
            self._youtube_trending(query),
            self._web_search(query, provider),
            self._wikipedia(query),
            self._rss(query),
            return_exceptions=True,
        )

        youtube_data, search_results, wiki_data, rss_items = [
            r if not isinstance(r, Exception) else [] for r in results
        ]

        # ── Build context string ───────────────────────────────
        context_parts: list[str] = []

        if youtube_data:
            context_parts.append("=== YOUTUBE TRENDING ===\n" + "\n".join(
                f"• {v['title']} ({v.get('views', '')})" for v in youtube_data[:5]
            ))

        if search_results:
            context_parts.append("=== WEB SEARCH ===\n" + "\n".join(
                f"• [{r.title}] {r.snippet}" for r in search_results[:8]
            ))

        if wiki_data:
            context_parts.append(f"=== WIKIPEDIA ===\n{wiki_data[:2000]}")

        if rss_items:
            context_parts.append("=== RSS FEEDS ===\n" + "\n".join(
                f"• {item['title']}" for item in rss_items[:5]
            ))

        raw_context = "\n\n".join(context_parts)
        sources = _build_sources(search_results, youtube_data)

        # ── LLM synthesis (if provider available) ─────────────
        if provider:
            brief = await self._synthesize(
                query=query,
                context=raw_context,
                brand=brand,
                provider=provider,
                sources=sources,
            )
        else:
            # Fallback: best-effort without LLM
            brief = ResearchBrief(
                topic=query,
                summary=raw_context[:500] if raw_context else "No data gathered.",
                key_points=[],
                suggested_angle="",
                sources=sources,
                confidence=0.5,
                raw_context=raw_context,
            )

        logger.info("research.done", topic=brief.topic, sources=len(brief.sources), confidence=brief.confidence)
        return brief

    # ── Sources ───────────────────────────────────────────────

    async def _youtube_trending(self, query: str) -> list[dict]:
        from research.sources.youtube import fetch_trending
        return await fetch_trending(query)

    async def _web_search(self, query: str, provider: Any) -> list:
        if provider is None:
            return []
        resolve_fn = getattr(provider, "resolve_or_none", None) or getattr(getattr(provider, "capabilities", None), "resolve_or_none", None)
        if not resolve_fn:
            return []
        search = resolve_fn(Capability.WEB_SEARCH)
        if not search:
            return []
        return await search.search(query, max_results=10)

    async def _wikipedia(self, query: str) -> str:
        from research.sources.wikipedia import fetch_summary
        return await fetch_summary(query)

    async def _rss(self, query: str) -> list[dict]:
        from research.sources.rss import fetch_feeds
        return await fetch_feeds(query)

    # ── LLM Synthesis ─────────────────────────────────────────

    async def _synthesize(
        self,
        query: str,
        context: str,
        brand: dict,
        provider: Any,
        sources: list[dict],
    ) -> ResearchBrief:
        resolve_fn = getattr(provider, "resolve", None) or getattr(getattr(provider, "capabilities", None), "resolve", None)
        llm = resolve_fn(Capability.TEXT_REASONING)
        result = await llm.chat_json([
            {
                "role": "system",
                "content": (
                    "You are a research analyst. Given raw gathered material, "
                    "synthesize a research brief. Return JSON:\n"
                    '{"topic": str, "summary": str (2-3 sentences), '
                    '"key_points": [str, ...], "suggested_angle": str, '
                    '"trending_score": float (0.0-1.0), "confidence": float (0.0-1.0)}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research query: {query}\n"
                    f"Brand: {brand.get('name', 'Unknown')}\n"
                    f"Target audience: {brand.get('target_audience', 'general')}\n\n"
                    f"{context}"
                ),
            },
        ])

        return ResearchBrief(
            topic=result.get("topic", query),
            summary=result.get("summary", ""),
            key_points=result.get("key_points", []),
            suggested_angle=result.get("suggested_angle", ""),
            sources=sources,
            trending_score=float(result.get("trending_score", 0.5)),
            confidence=float(result.get("confidence", 0.85)),
            raw_context=context,
        )


def _build_sources(search_results: list, youtube_data: list) -> list[dict[str, str]]:
    sources = []
    if isinstance(search_results, list):
        for r in search_results[:5]:
            if hasattr(r, "title") and hasattr(r, "url"):
                sources.append({"title": r.title, "url": r.url, "type": "web"})
    if isinstance(youtube_data, list):
        for v in youtube_data[:3]:
            if isinstance(v, dict):
                sources.append({"title": v.get("title", ""), "url": v.get("url", ""), "type": "youtube"})
    return sources


# Singleton
research_engine = ResearchEngine()
