"""
API Discovery Tool
Adapted from Anchorgrid-hub (anchorgrid/tools/api_discovery.py)

Opens any URL in a headless browser, intercepts all XHR/Fetch requests,
and surfaces undocumented JSON API endpoints with sample responses.

Used by the Research Engine to discover live data from:
  - YouTube trending
  - Google Trends
  - Reddit
  - Any dynamic web page

Requires: playwright install chromium
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

import structlog

logger = structlog.get_logger()


class APIDiscovery:
    """Discover undocumented APIs by monitoring browser network traffic."""

    def __init__(self) -> None:
        self.discovered_apis: list[dict[str, Any]] = []
        self.json_endpoints: list[dict[str, Any]] = []

    async def discover(
        self,
        url: str,
        wait_seconds: int = 5,
        interactions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Visit URL, capture all XHR/fetch JSON responses.

        Args:
            url: Page to inspect
            wait_seconds: Wait time after load for dynamic content
            interactions: Optional CSS selectors to click (triggers lazy loads)

        Returns:
            List of discovered JSON endpoints with sample responses
        """
        logger.info("api_discovery.start", url=url)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("api_discovery.playwright_missing")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            async def handle_response(response: Any) -> None:
                if response.request.resource_type not in ("xhr", "fetch"):
                    return
                try:
                    content_type = response.headers.get("content-type", "")
                    if "json" not in content_type:
                        return
                    body = await response.text()
                    data = json.loads(body)
                    self.json_endpoints.append({
                        "method":          response.request.method,
                        "url":             response.url,
                        "status":          response.status,
                        "headers":         dict(response.headers),
                        "sample_response": data,
                        "timestamp":       datetime.now().isoformat(),
                    })
                    logger.debug("api_discovery.found", url=response.url)
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="load", timeout=30_000)
            except Exception as exc:
                logger.warning("api_discovery.load_timeout", error=str(exc))

            await asyncio.sleep(wait_seconds)

            if interactions:
                for selector in interactions:
                    try:
                        await page.click(selector)
                        await asyncio.sleep(1)
                    except Exception:
                        pass

            await browser.close()

        logger.info("api_discovery.done", endpoints=len(self.json_endpoints))
        return self.json_endpoints

    def extract_data_urls(
        self,
        filter_keywords: list[str] | None = None,
    ) -> list[str]:
        """Return just the URLs, optionally filtered by keyword."""
        urls = [e["url"] for e in self.json_endpoints]
        if filter_keywords:
            urls = [
                u for u in urls
                if any(kw.lower() in u.lower() for kw in filter_keywords)
            ]
        return urls

    def save_report(self, path: str) -> None:
        Path(path).write_text(
            json.dumps(
                {
                    "discovered": len(self.json_endpoints),
                    "endpoints": self.json_endpoints,
                },
                indent=2,
                default=str,
            )
        )
