"""
runtime/capabilities.py

Capability vocabulary for Animus Studio.
Describes what is needed, never how to obtain it.

See ARCHITECTURE_v1.md for the full capability contract.
"""
from __future__ import annotations
from enum import Enum


class Capability(str, Enum):
    # Language
    TEXT_GENERATION      = "text_generation"
    TEXT_REASONING       = "text_reasoning"
    VISION_UNDERSTANDING = "vision_understanding"
    TEXT_EMBEDDING       = "text_embedding"

    # Audio
    VOICE_SYNTHESIS      = "voice_synthesis"
    VOICE_TRANSCRIPTION  = "voice_transcription"

    # Web
    WEB_SEARCH           = "web_search"
    WEB_SCRAPING         = "web_scraping"
    BROWSER              = "browser"

    # Media
    IMAGE_GENERATION     = "image_generation"
    VIDEO_ASSEMBLY       = "video_assembly"

    # Compute
    CODE                 = "code"
    TERMINAL             = "terminal"

    # Studio
    PUBLISH              = "publish"
    MEMORY               = "memory"
    ANALYTICS            = "analytics"


# Human-readable metadata for doctor output and error messages
CAPABILITY_META: dict[Capability, dict] = {
    Capability.TEXT_GENERATION:      {"label": "Text Generation",       "suggest": "Set OLLAMA_HOST or add OPENAI_API_KEY"},
    Capability.TEXT_REASONING:       {"label": "Text Reasoning",        "suggest": "ollama pull deepseek-r1:8b"},
    Capability.VISION_UNDERSTANDING: {"label": "Vision Understanding",  "suggest": "ollama pull llava"},
    Capability.TEXT_EMBEDDING:       {"label": "Text Embedding",        "suggest": "ollama pull nomic-embed-text"},
    Capability.VOICE_SYNTHESIS:      {"label": "Voice Synthesis",       "suggest": "pip install kokoro-onnx soundfile"},
    Capability.VOICE_TRANSCRIPTION:  {"label": "Voice Transcription",   "suggest": "Set WHISPER_MODEL=small"},
    Capability.WEB_SEARCH:           {"label": "Web Search",            "suggest": "pip install duckduckgo-search (no key needed)"},
    Capability.WEB_SCRAPING:         {"label": "Web Scraping",          "suggest": "playwright install chromium"},
    Capability.BROWSER:              {"label": "Browser Control",       "suggest": "playwright install chromium"},
    Capability.IMAGE_GENERATION:     {"label": "Image Generation",      "suggest": "Pillow templates available by default"},
    Capability.VIDEO_ASSEMBLY:       {"label": "Video Assembly",        "suggest": "pip install moviepy (requires ffmpeg)"},
    Capability.CODE:                 {"label": "Code Execution",        "suggest": "Built-in (sandboxed)"},
    Capability.TERMINAL:             {"label": "Terminal Execution",    "suggest": "Built-in (guarded)"},
    Capability.PUBLISH:              {"label": "Publishing",            "suggest": "Configure platform credentials in .env"},
    Capability.MEMORY:               {"label": "Memory (pgvector)",     "suggest": "Requires DATABASE_URL with pgvector extension"},
    Capability.ANALYTICS:            {"label": "Analytics",             "suggest": "Built-in"},
}
