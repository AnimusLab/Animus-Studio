"""
Memory type definitions for Animus Studio's Knowledge Engine.

Five memory layers:
    Creator  — voice, vocabulary, writing style, fill words
    Brand    — tone, identity, rules, target audience
    Audience — observed preferences, top comments, engagement signals
    Video    — past script patterns, successful hooks, failed angles
    Platform — per-platform performance rules and formatting constraints
"""
from __future__ import annotations
from enum import StrEnum
from dataclasses import dataclass, field
from typing import Any


class MemoryType(StrEnum):
    CREATOR  = "creator"
    BRAND    = "brand"
    AUDIENCE = "audience"
    VIDEO    = "video"
    PLATFORM = "platform"


@dataclass
class MemoryEntry:
    """A single piece of knowledge stored in the vector DB."""
    brand_id: str
    type: MemoryType
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    # Populated after DB write
    id: str | None = None
    embedding: list[float] | None = None


@dataclass
class MemorySearchResult:
    entry: MemoryEntry
    score: float   # cosine similarity 0–1


# ─── Well-known memory templates ──────────────────────────────

CREATOR_MEMORY_TEMPLATE = """
Creator: {name}
Vocabulary: {vocabulary}
Sentence style: {sentence_style}
Fill words: {fill_words}
Average sentence length: {avg_sentence_len} words
Preferred openers: {preferred_openers}
Tone: {tone}
""".strip()

BRAND_MEMORY_TEMPLATE = """
Brand: {name}
Mission: {mission}
Target audience: {target_audience}
Tone: {tone}
Avoid: {avoid}
Preferred content formats: {preferred_formats}
Platform focus: {platforms}
""".strip()

VIDEO_MEMORY_TEMPLATE = """
Title: {title}
Hook: {hook}
Outcome: {outcome}
Views: {views}
CTR: {ctr}%
Avg retention: {retention}%
What worked: {worked}
What failed: {failed}
Lesson: {lesson}
""".strip()

AUDIENCE_MEMORY_TEMPLATE = """
Platform: {platform}
Observation: {observation}
Engagement signal: {engagement_signal}
Top comments: {top_comments}
Preferred topics: {preferred_topics}
Avoid: {avoid}
""".strip()

PLATFORM_MEMORY_TEMPLATE = """
Platform: {platform}
Best posting times: {best_times}
Optimal video length: {optimal_length}
Best CTR thumbnail style: {thumbnail_style}
Caption style: {caption_style}
Hashtag strategy: {hashtag_strategy}
""".strip()
