"""
runtime/integrations/youtube/connection.py

YouTubeConnection — Encapsulates an active, auto-refreshing YouTube channel connection.
"""
from __future__ import annotations
from typing import Any
from runtime.integrations.base_connection import BaseConnection


class YouTubeConnection(BaseConnection):
    """
    YouTube channel connection object returned by integration_manager.get_connection("youtube", brand_id).
    """

    async def get_channel_info(self) -> dict[str, Any]:
        """Fetch live channel metadata using current access_token."""
        from runtime.integrations.youtube.oauth import youtube_oauth
        return await youtube_oauth.fetch_channel_info(self.access_token)

    async def is_healthy(self) -> bool:
        """Check if token can reach YouTube API."""
        info = await self.get_channel_info()
        return "error" not in info
