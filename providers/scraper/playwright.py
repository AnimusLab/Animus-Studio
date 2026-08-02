"""
providers/scraper/playwright.py

Playwright browser provider.
Handles BROWSER and WEB_SCRAPING capabilities.

Requires: playwright install chromium
"""
from __future__ import annotations
from typing import Any
from runtime.capabilities import Capability
from providers.health_contract import HealthCheckMixin, HealthCheckResult


class PlaywrightBrowser(HealthCheckMixin):
    """Headless Chromium via Playwright."""

    name = "playwright"
    priority = 10
    is_cloud = False
    capabilities = {Capability.BROWSER, Capability.WEB_SCRAPING}
    model = "playwright/chromium"

    def __init__(self) -> None:
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from playwright.async_api import async_playwright  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False
        return self._available

    async def _healthcheck(self) -> HealthCheckResult:
        """
        Real test: launch Chromium, navigate to example.com, read body text.
        Chromium must be installed (playwright install chromium).
        """
        if not self.is_available():
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="Playwright package not installed",
                error="playwright not importable",
                metadata={"fix": "pip install playwright && playwright install chromium"},
            )

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("https://example.com", wait_until="load", timeout=20_000)
                title = await page.title()
                text_snippet = (await page.inner_text("body"))[:80].strip()
                await browser.close()

            if not title:
                raise ValueError("Empty page title returned")

            return HealthCheckResult(
                ok=True,
                name=self.name,
                detail=f"Navigated to example.com — title: '{title}'",
                metadata={"title": title, "body_preview": text_snippet},
            )
        except Exception as exc:
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="Browser launch or navigation failed",
                error=str(exc),
                metadata={"fix": "playwright install chromium"},
            )

    async def fetch_page(
        self,
        url: str,
        wait_seconds: int = 3,
        selector: str | None = None,
    ) -> str:
        import asyncio
        from playwright.async_api import async_playwright

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

            try:
                await page.goto(url, wait_until="load", timeout=30_000)
            except Exception:
                pass

            await asyncio.sleep(wait_seconds)

            if selector:
                try:
                    el = page.locator(selector).first
                    text = await el.inner_text()
                except Exception:
                    text = await page.inner_text("body")
            else:
                text = await page.inner_text("body")

            await browser.close()
            return text

    async def screenshot(self, url: str, output_path: str) -> str:
        from pathlib import Path
        from playwright.async_api import async_playwright

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()
            await page.goto(url, wait_until="load", timeout=30_000)
            await page.screenshot(path=output_path, full_page=True)
            await browser.close()

        return output_path
