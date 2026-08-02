"""
runtime/services/metadata.py

MetadataGenerator service.
Synthesizes a generic, canonical PublishingPackage from script and research artifacts.
Does NOT perform platform-specific string formatting (formatting is handled by platform publishers).
"""
from __future__ import annotations
from typing import Any
from runtime.brand import Brand, ANIMUSLAB_BRAND
from runtime.publishing.package import PublishingPackage


class MetadataGenerator:
    """
    Synthesizes universal PublishingPackage instances from raw script & brief artifacts.
    """

    def create_package(
        self,
        script: dict[str, Any],
        brief: dict[str, Any] | None = None,
        brand: Brand | None = None,
        video_path: str = "",
        thumbnail_path: str | None = None,
    ) -> PublishingPackage:
        brand = brand or ANIMUSLAB_BRAND
        brief = brief or {}

        title = script.get("title") or brief.get("topic") or "Untitled Animus Video"
        description = script.get("description") or script.get("summary") or brief.get("summary") or ""
        raw_tags = script.get("tags") or brief.get("key_points") or []

        # Merge script tags with Brand default_tags
        tags_set = list(dict.fromkeys(list(brand.default_tags) + list(raw_tags)))

        # Extract chapters if present in script
        chapters_raw = script.get("chapters", [])
        chapters = tuple(chapters_raw) if isinstance(chapters_raw, list) else ()

        # Extract hashtags
        hashtags_raw = script.get("hashtags", [f"#{tag.replace(' ', '')}" for tag in tags_set[:5]])
        hashtags = tuple(hashtags_raw) if isinstance(hashtags_raw, list) else ()

        # Get brand publishing defaults
        defaults = brand.publishing_defaults

        return PublishingPackage(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=title.strip(),
            description=description.strip(),
            tags=tuple(tags_set),
            hashtags=hashtags,
            chapters=chapters,
            visibility=defaults.get("visibility", "private"),
            category=defaults.get("category", "28"),
            language=defaults.get("language", "en"),
            made_for_kids=defaults.get("made_for_kids", False),
            metadata={
                "brand_id": brand.id,
                "topic": brief.get("topic", ""),
                "suggested_angle": brief.get("suggested_angle", ""),
            },
        )


metadata_generator = MetadataGenerator()
