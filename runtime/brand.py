"""
runtime/brand.py

Brand domain model & global BrandRegistry.
Immutable (frozen=True). Acts as execution context for missions, rendering, and publishing.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Brand:
    """
    Brand execution context. Holds brand identity, styling, audio narrator,
    intro/outro assets, and default publishing configurations.
    """
    id: str                                  # 'AnimusLab', 'Anchor', 'Canon'
    name: str
    target_audience: str
    tone: str                                # 'authoritative', 'casual'
    narrator: str = "kokoro:af_heart"
    thumbnail_theme: str = "animus_dark"
    logo_path: str | None = None
    intro_path: str | None = None
    outro_path: str | None = None
    default_tags: tuple[str, ...] = field(default_factory=tuple)
    publishing_defaults: dict[str, Any] = field(default_factory=lambda: {
        "visibility": "private",
        "category": "28",  # Science & Tech
        "language": "en",
        "made_for_kids": False,
    })


# Built-in Brand Profiles
ANIMUSLAB_BRAND = Brand(
    id="AnimusLab",
    name="AnimusLab Engineering",
    target_audience="Software Engineers & AI Architects",
    tone="authoritative",
    narrator="kokoro:af_heart",
    thumbnail_theme="animus_cyberpunk",
    default_tags=("AI", "SoftwareEngineering", "SystemArchitecture", "Python"),
    publishing_defaults={
        "visibility": "private",
        "category": "28",
        "language": "en",
        "made_for_kids": False,
    },
)

ANCHOR_BRAND = Brand(
    id="Anchor",
    name="Anchor Governance",
    target_audience="Security Engineers & Compliance Leads",
    tone="formal",
    narrator="kokoro:am_adam",
    thumbnail_theme="anchor_navy",
    default_tags=("Security", "Compliance", "AIGovernance"),
    publishing_defaults={
        "visibility": "private",
        "category": "28",
        "language": "en",
        "made_for_kids": False,
    },
)


class BrandRegistry:
    """Registry for retrieving configured Brand execution contexts."""

    def __init__(self) -> None:
        self._brands: dict[str, Brand] = {
            "animuslab": ANIMUSLAB_BRAND,
            "anchor": ANCHOR_BRAND,
        }

    def get(self, brand_id: str = "AnimusLab") -> Brand:
        key = brand_id.lower()
        if key in self._brands:
            return self._brands[key]
        # Return fallback Brand if custom brand_id requested
        return Brand(id=brand_id, name=brand_id, target_audience="general", tone="professional")

    def register(self, brand: Brand) -> None:
        self._brands[brand.id.lower()] = brand


brand_registry = BrandRegistry()
