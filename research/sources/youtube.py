"""YouTube trending — public RSS, no API key required"""
from __future__ import annotations
import httpx
import xml.etree.ElementTree as ET


async def fetch_trending(query: str) -> list[dict]:
    """
    Fetch YouTube search results via the public RSS feed.
    No API key required.
    """
    url = f"https://www.youtube.com/feeds/videos.xml?search_query={query.replace(' ', '+')}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

        ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        root = ET.fromstring(resp.text)
        videos = []
        for entry in root.findall("atom:entry", ns)[:10]:
            title = entry.findtext("atom:title", "", ns)
            link  = entry.find("atom:link", ns)
            url_  = link.get("href", "") if link is not None else ""
            videos.append({"title": title, "url": url_, "views": ""})
        return videos
    except Exception:
        return []
