"""
runtime/publishing/publishers/youtube.py

YouTubePublisher plugin #1.
Renders PublishingPackage according to YouTubeCapabilities and performs resumable uploads
to YouTube Data API v3 in private mode.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any
import httpx
import structlog

from runtime.integrations.base_connection import BaseConnection
from runtime.publishing.capabilities import YOUTUBE_CAPABILITIES, PlatformCapabilities
from runtime.publishing.package import PublishingPackage
from runtime.publishing.publishers.base import BasePublisher
from runtime.publishing.result import PublishingResult

logger = structlog.get_logger()


class YouTubePublisher(BasePublisher):
    """
    YouTube platform publisher plugin.
    Renders chapters, hashtags, and description text according to YOUTUBE_CAPABILITIES.
    Uploads video file via YouTube Data API v3 resumable upload protocol.
    """
    provider = "youtube"
    capabilities: PlatformCapabilities = YOUTUBE_CAPABILITIES

    def __init__(self) -> None:
        self._log = logger.bind(publisher="YouTubePublisher")

    def render_description(self, package: PublishingPackage) -> str:
        """Render YouTube-formatted description text including chapters and hashtags."""
        parts = [package.description.strip()]

        # Format chapter timestamps if present and supported
        if package.chapters and self.capabilities.supports_chapters:
            parts.append("\n\n─── Chapters ───")
            for ch in package.chapters:
                time_str = ch.get("time", "00:00")
                ch_title = ch.get("title", "")
                parts.append(f"{time_str} {ch_title}")

        # Format hashtags
        if package.hashtags:
            tag_str = " ".join([h if h.startswith("#") else f"#{h}" for h in package.hashtags])
            parts.append(f"\n\n{tag_str}")

        full_desc = "\n".join(parts).strip()
        # Enforce max_description_length boundary
        return full_desc[: self.capabilities.max_description_length]

    async def publish(
        self,
        package: PublishingPackage,
        connection: BaseConnection,
        brand_id: str = "default",
    ) -> PublishingResult:
        """
        Upload video file to YouTube Data API v3 in private mode.
        """
        if not package.video_path or not os.path.exists(package.video_path):
            return PublishingResult(
                provider=self.provider,
                brand_id=brand_id,
                status="failed",
                error=f"Video file not found: {package.video_path}",
            )

        title = package.title[: self.capabilities.max_title_length]
        description = self.render_description(package)
        access_token = connection.access_token

        self._log.info(
            "youtube.upload.started",
            title=title,
            visibility=package.visibility,
            brand_id=brand_id,
        )

        try:
            # Metadata snippet for YouTube API
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": list(package.tags),
                    "categoryId": package.category,
                    "defaultLanguage": package.language,
                },
                "status": {
                    "privacyStatus": package.visibility,
                    "selfDeclaredMadeForKids": package.made_for_kids,
                },
            }

            # 1. Initiate Resumable Upload Session
            init_url = (
                "https://www.googleapis.com/upload/youtube/v3/videos?"
                "uploadType=resumable&part=snippet,status"
            )
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "video/mp4",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                init_resp = await client.post(init_url, headers=headers, json=body)
                init_resp.raise_for_status()

                upload_url = init_resp.headers.get("Location")
                if not upload_url:
                    raise RuntimeError("Failed to receive upload session Location header from YouTube API")

                # 2. Stream Video Bytes to Resumable Upload URL
                video_size = os.path.getsize(package.video_path)
                with open(package.video_path, "rb") as f:
                    video_bytes = f.read()

                put_headers = {
                    "Content-Type": "video/mp4",
                    "Content-Length": str(video_size),
                }

                upload_resp = await client.put(upload_url, headers=put_headers, content=video_bytes)
                upload_resp.raise_for_status()
                data = upload_resp.json()

            video_id = data.get("id", "")
            video_url = f"https://youtu.be/{video_id}"
            studio_url = f"https://studio.youtube.com/video/{video_id}/edit"

            self._log.info("youtube.upload.completed", video_id=video_id, url=video_url)

            return PublishingResult(
                provider=self.provider,
                brand_id=brand_id,
                status="uploaded",
                video_id=video_id,
                url=video_url,
                studio_url=studio_url,
                visibility=package.visibility,
                metadata={
                    "channel_name": connection.account_name,
                    "formatted_title": title,
                    "category": package.category,
                },
            )

        except Exception as exc:
            self._log.error("youtube.upload.failed", error=str(exc))
            return PublishingResult(
                provider=self.provider,
                brand_id=brand_id,
                status="failed",
                visibility=package.visibility,
                error=str(exc),
            )
