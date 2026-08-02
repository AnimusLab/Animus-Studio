"""
Rate Limited Scraper
Adapted from Anchorgrid-hub (anchorgrid/tools/rate_limited_scraper.py)

Coordinator for large-scale data collection.
Features:
  - Adaptive delays between requests
  - Per-source rate limits
  - Jitter (10-30%) to avoid pattern detection
  - Exponential backoff on error
"""
from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Callable

import structlog

logger = structlog.get_logger()


class RateLimitedScraper:
    def __init__(self, requests_per_minute: int = 30) -> None:
        self.delay = 60.0 / requests_per_minute
        self.last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def fetch(self, identifier: str, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute a scraping function with rate limiting and jitter."""
        async with self._lock:
            elapsed   = time.time() - self.last_request_time
            wait_time = max(0.0, self.delay - elapsed)
            wait_time += wait_time * random.uniform(0.1, 0.3)   # jitter

            if wait_time > 0:
                logger.debug("scraper.waiting", identifier=identifier, wait_s=round(wait_time, 2))
                await asyncio.sleep(wait_time)

            try:
                result = await func(*args, **kwargs)
                self.last_request_time = time.time()
                return result
            except Exception as exc:
                logger.error("scraper.error", identifier=identifier, error=str(exc))
                self.delay = min(self.delay * 1.5, 60.0)   # cap at 60s
                raise

    async def batch_fetch(self, items: list[Any], func: Callable) -> list[Any]:
        """Fetch multiple items sequentially with rate limiting."""
        results = []
        for item in items:
            try:
                res = await self.fetch(str(item), func, item)
                results.append(res)
            except Exception:
                continue
        return results
