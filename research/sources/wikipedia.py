"""Wikipedia REST API — free, no key"""
from __future__ import annotations
import httpx


async def fetch_summary(query: str) -> str:
    """Fetch Wikipedia page summary for a topic."""
    title = query.replace(" ", "_")
    url   = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "AnimusStudio/1.0"})
            if resp.status_code == 200:
                return resp.json().get("extract", "")
    except Exception:
        pass
    return ""
