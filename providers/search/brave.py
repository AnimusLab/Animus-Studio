"""Brave Search Provider — optional"""
from __future__ import annotations
import os
from providers.search.base import BaseSearchProvider, SearchResult


class BraveProvider(BaseSearchProvider):
    name = "brave"
    priority = 30
    is_cloud = True
    model = "brave"


    def __init__(self) -> None:
        self._key = os.getenv("BRAVE_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._key)

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"Accept": "application/json", "X-Subscription-Token": self._key},
                params={"q": query, "count": max_results},
            )
            resp.raise_for_status()
            data = resp.json()
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("description", ""),
                source="brave",
            )
            for r in data.get("web", {}).get("results", [])
        ]
