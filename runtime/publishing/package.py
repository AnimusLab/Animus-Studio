"""
runtime/publishing/package.py

Canonical PublishingPackage domain object.
Immutable (frozen=True). Represents the universal publishing payload across all platforms.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class PublishingPackage:
    """
    Immutable, platform-agnostic publishing payload.
    Renderer plugins (YouTubePublisher, InstagramPublisher, etc.) format this
    package according to their specific PlatformCapabilities.
    """
    video_path: str
    thumbnail_path: str | None = None
    captions_path: str | None = None
    title: str = ""
    description: str = ""
    hashtags: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    chapters: tuple[dict[str, str], ...] = field(default_factory=tuple) # ({"time": "00:00", "title": "Intro"},)
    playlist: str | None = None
    visibility: str = "private"
    category: str = "28"  # Science & Tech
    language: str = "en"
    made_for_kids: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_title(self, title: str) -> PublishingPackage:
        return replace(self, title=title)

    def with_description(self, description: str) -> PublishingPackage:
        return replace(self, description=description)

    def with_visibility(self, visibility: str) -> PublishingPackage:
        return replace(self, visibility=visibility)

    def with_metadata(self, **kwargs: Any) -> PublishingPackage:
        new_meta = {**self.metadata, **kwargs}
        return replace(self, metadata=new_meta)
