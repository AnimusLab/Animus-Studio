"""
runtime/publishing/capabilities.py

PlatformCapabilities model & pre-built provider capability matrices.
Immutable (frozen=True). Defines what each social platform supports.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformCapabilities:
    """
    Defines feature availability and constraint limits for a social platform.
    Used by publishers to validate and format PublishingPackage instances.
    """
    provider: str
    supports_video: bool = True
    supports_shorts: bool = False
    supports_chapters: bool = False
    supports_playlists: bool = False
    supports_carousels: bool = False
    supports_articles: bool = False
    supports_drafts: bool = True
    max_title_length: int = 100
    max_description_length: int = 5000
    max_video_size_bytes: int = 128 * 1024 * 1024 * 1024  # 128GB


# Pre-built capability matrices
YOUTUBE_CAPABILITIES = PlatformCapabilities(
    provider="youtube",
    supports_video=True,
    supports_shorts=True,
    supports_chapters=True,
    supports_playlists=True,
    supports_drafts=True,
    max_title_length=100,
    max_description_length=5000,
)

INSTAGRAM_CAPABILITIES = PlatformCapabilities(
    provider="instagram",
    supports_video=True,
    supports_shorts=True,
    supports_carousels=True,
    supports_chapters=False,
    supports_playlists=False,
    supports_drafts=True,
    max_title_length=0,  # Instagram uses captions only
    max_description_length=2200,
)

LINKEDIN_CAPABILITIES = PlatformCapabilities(
    provider="linkedin",
    supports_video=True,
    supports_articles=True,
    supports_chapters=False,
    supports_playlists=False,
    supports_drafts=True,
    max_title_length=200,
    max_description_length=3000,
)

TWITTER_CAPABILITIES = PlatformCapabilities(
    provider="twitter",
    supports_video=True,
    supports_chapters=False,
    supports_playlists=False,
    supports_drafts=True,
    max_title_length=0,
    max_description_length=280,
)
