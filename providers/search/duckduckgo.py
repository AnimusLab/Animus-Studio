"""
DuckDuckGo Search Provider — free, no key required, default

Package was renamed from `duckduckgo-search` to `ddgs`.
Requires: pip install ddgs
"""
from __future__ import annotations
from providers.search.base import BaseSearchProvider, SearchResult
from providers.health_contract import HealthCheckMixin, HealthCheckResult


class DuckDuckGoProvider(HealthCheckMixin, BaseSearchProvider):
    name = "duckduckgo"
    priority = 10
    is_cloud = False
    model = "duckduckgo"

    def is_available(self) -> bool:
        try:
            from ddgs import DDGS  # noqa: F401
            return True
        except ImportError:
            try:
                from duckduckgo_search import DDGS  # noqa: F401
                return True
            except ImportError:
                return False

    async def _healthcheck(self) -> HealthCheckResult:
        """
        Real test: search("hello world") and expect at least 1 result back.
        """
        if not self.is_available():
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="Package missing",
                error="ddgs not installed",
                metadata={"fix": "pip install ddgs"},
            )

        try:
            results = await self.search("hello world", max_results=1)
            if not results:
                raise ValueError("Zero results returned")
            return HealthCheckResult(
                ok=True,
                name=self.name,
                detail=f"Search OK — returned {len(results)} result(s)",
                metadata={"first_url": results[0].url if results else ""},
            )
        except Exception as exc:
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="Search request failed",
                error=str(exc),
            )

    def _get_ddgs(self):
        """Return DDGS class, preferring new `ddgs` package."""
        try:
            from ddgs import DDGS
            return DDGS
        except ImportError:
            from duckduckgo_search import DDGS
            return DDGS

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        import asyncio

        DDGS = self._get_ddgs()

        def _run() -> list[SearchResult]:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source="duckduckgo",
                    ))
            return results

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)
