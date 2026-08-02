"""RSS feed aggregator — free, no key required"""
from __future__ import annotations
import httpx


# Curated RSS feeds relevant to tech / AI / business content
DEFAULT_FEEDS = [
    "https://feeds.feedburner.com/TechCrunch",
    "https://www.wired.com/feed/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.theverge.com/rss/index.xml",
]


async def fetch_feeds(query: str, feeds: list[str] | None = None) -> list[dict]:
    """
    Parse RSS feeds and return items whose title/description
    contains words from the query.
    """
    import xml.etree.ElementTree as ET
    import asyncio

    feeds = feeds or DEFAULT_FEEDS
    query_words = set(query.lower().split())

    async def _fetch_one(feed_url: str) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
            root = ET.fromstring(resp.text)
            items = []
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                link  = (item.findtext("link") or "").strip()
                text  = (title + " " + desc).lower()
                if any(w in text for w in query_words):
                    items.append({"title": title, "url": link, "snippet": desc[:200]})
            return items
        except Exception:
            return []

    results = await asyncio.gather(*[_fetch_one(f) for f in feeds])
    merged = [item for sublist in results for item in sublist]
    return merged[:10]
