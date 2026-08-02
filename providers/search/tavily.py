"""Tavily Search Provider — optional, AI-optimized results"""
from __future__ import annotations
import os
from providers.search.base import BaseSearchProvider, SearchResult


class TavilyProvider(BaseSearchProvider):
    name = "tavily"
    priority = 20
    is_cloud = True
    model = "tavily"


    def __init__(self) -> None:
        self._key = os.getenv("TAVILY_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._key)

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": self._key, "query": query, "max_results": max_results},
            )
            resp.raise_for_status()
            data = resp.json()
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                source="tavily",
            )
            for r in data.get("results", [])
        ]
