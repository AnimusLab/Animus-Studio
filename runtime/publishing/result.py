"""
runtime/publishing/result.py

Standardized PublishingResult domain object.
Immutable (frozen=True). Returned by all platform publishers upon upload completion.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PublishingResult:
    """
    Canonical output returned by any publisher (YouTubePublisher, InstagramPublisher, etc.).
    """
    provider: str
    brand_id: str
    status: str            # 'uploaded', 'published', 'failed'
    video_id: str | None = None
    url: str | None = None
    studio_url: str | None = None
    visibility: str = "private"
    upload_time: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("uploaded", "published") and not self.error
