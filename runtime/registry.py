"""
runtime/registry.py

The Runtime kernel. One instance per Studio process.

Workers call:
    runtime.capabilities.resolve(Capability.TEXT_REASONING)

Never:
    from providers.llm.ollama import OllamaProvider
"""
from __future__ import annotations

import os
from typing import Any

import structlog

from runtime.capabilities import Capability, CAPABILITY_META

logger = structlog.get_logger()


# ─── Exceptions ────────────────────────────────────────────────

class CapabilityUnavailableError(RuntimeError):
    def __init__(self, capability: Capability) -> None:
        meta = CAPABILITY_META.get(capability, {})
        super().__init__(
            f"Capability unavailable: {meta.get('label', capability.value)}\n"
            f"Suggestion: {meta.get('suggest', 'Check .env configuration')}"
        )
        self.capability = capability


# ─── ProviderRegistry ──────────────────────────────────────────

class ProviderRegistry:
    """
    AI model providers only.
    Owned by CapabilityRegistry. Not called directly by workers.
    Providers self-declare their name, default priority, and capabilities.
    """

    def __init__(self) -> None:
        self._providers: dict[Capability, list[Any]] = {}
        self._resolved:  dict[Capability, Any] = {}

    def register(self, provider: Any) -> None:
        """Register a provider based on its self-declared capabilities."""
        for cap in getattr(provider, "capabilities", []):
            self._providers.setdefault(cap, [])
            if provider not in self._providers[cap]:
                self._providers[cap].append(provider)

    def _get_effective_priority(self, provider: Any, capability: Capability) -> float:
        base_priority = getattr(provider, "priority", 100)
        p_name = getattr(provider, "name", "").lower()
        p_is_cloud = getattr(provider, "is_cloud", False)

        # Voice provider override from .env
        if capability == Capability.VOICE_SYNTHESIS:
            voice_override = os.getenv("VOICE_PROVIDER", "auto").lower().strip()
            if voice_override != "auto" and p_name == voice_override:
                return -1000.0  # Explicit env override wins first

        # Cloud models promotion if ENABLE_CLOUD_MODELS=true
        if p_is_cloud:
            enable_cloud = os.getenv("ENABLE_CLOUD_MODELS", "false").lower() == "true"
            if enable_cloud:
                return float(base_priority - 100.0)

        return float(base_priority)

    def resolve(self, capability: Capability) -> Any:
        if capability in self._resolved:
            return self._resolved[capability]

        candidates = self._providers.get(capability, [])
        # Data-driven priority sort
        sorted_candidates = sorted(
            candidates,
            key=lambda p: self._get_effective_priority(p, capability)
        )

        for p in sorted_candidates:
            if p.is_available():
                self._resolved[capability] = p
                return p

        raise CapabilityUnavailableError(capability)

    def resolve_or_none(self, capability: Capability) -> Any | None:
        try:
            return self.resolve(capability)
        except CapabilityUnavailableError:
            return None

    def candidates(self, capability: Capability) -> list[Any]:
        candidates = self._providers.get(capability, [])
        return sorted(
            candidates,
            key=lambda p: self._get_effective_priority(p, capability)
        )

    def invalidate_cache(self) -> None:
        self._resolved.clear()


# ─── CapabilityRegistry ────────────────────────────────────────

class CapabilityRegistry:
    """
    Resolves any capability — AI providers, tools, or runtime services.
    Workers always call this, never ProviderRegistry directly.
    """

    def __init__(self, providers: ProviderRegistry) -> None:
        self._providers = providers
        # Non-AI capability implementations registered separately
        self._tools: dict[Capability, Any] = {}

    def register_tool(self, capability: Capability, impl: Any) -> None:
        """Register a non-AI tool for a capability (e.g. ffmpeg for VIDEO_ASSEMBLY)."""
        self._tools[capability] = impl

    def resolve(self, capability: Capability) -> Any:
        # Non-AI tools take precedence for their specific capabilities
        if capability in self._tools:
            impl = self._tools[capability]
            if callable(getattr(impl, "is_available", None)) and not impl.is_available():
                raise CapabilityUnavailableError(capability)
            return impl
        # Fall through to AI providers
        return self._providers.resolve(capability)

    def resolve_or_none(self, capability: Capability) -> Any | None:
        try:
            return self.resolve(capability)
        except CapabilityUnavailableError:
            return None

    def health(self) -> dict[Capability, dict]:
        results: dict[Capability, dict] = {}
        for cap in Capability:
            try:
                impl = self.resolve(cap)
                results[cap] = {
                    "status": "ok",
                    "provider": getattr(impl, "name", type(impl).__name__),
                    "model": getattr(impl, "model", None),
                }
            except CapabilityUnavailableError:
                results[cap] = {"status": "unavailable", "provider": None, "model": None}
        return results


# ─── Runtime (the kernel) ──────────────────────────────────────

class Runtime:
    """
    The Studio kernel. One instance per process.
    Initialised once at startup, injected into RuntimeContext.
    """

    def __init__(self) -> None:
        self.providers    = ProviderRegistry()
        self.capabilities = CapabilityRegistry(self.providers)
        self.credentials: Any  = None   # set by _bootstrap()
        self.events:      Any  = None   # set by _bootstrap()
        self.memory:      Any  = None   # set by _bootstrap()
        self.scheduler:   Any  = None   # stub in v1
    def resolve(self, capability: Capability) -> Any:
        return self.capabilities.resolve(capability)

    def resolve_or_none(self, capability: Capability) -> Any | None:
        return self.capabilities.resolve_or_none(capability)

    async def bootstrap(self) -> None:
        """Called once at startup. Registers all providers and services."""
        if self._ready:
            return

        try:
            from app.core.config import settings
        except ImportError:
            from backend.app.core.config import settings
        self.config = settings

        self._register_ai_providers()
        self._register_tools()

        from runtime.credentials import CredentialManager
        self.credentials = CredentialManager()

        from runtime.eventbus import EventBus
        self.events = EventBus()

        from runtime.storage import LocalArtifactStore
        self.storage = LocalArtifactStore(
            base_path=getattr(self.config, "storage_local_path", "./storage")
        )

        self._ready = True
        logger.info("runtime.ready")


    def _register_ai_providers(self) -> None:
        from providers.llm.ollama      import OllamaProvider
        from providers.llm.openai      import OpenAIProvider
        from providers.llm.anthropic   import AnthropicProvider
        from providers.llm.groq        import GroqProvider
        from providers.llm.openrouter  import OpenRouterProvider
        from providers.voice.kokoro     import KokoroProvider
        from providers.voice.piper      import PiperProvider
        from providers.voice.elevenlabs import ElevenLabsProvider
        from providers.search.duckduckgo import DuckDuckGoProvider
        from providers.search.tavily      import TavilyProvider
        from providers.search.brave       import BraveProvider
        from providers.image.pillow       import PillowProvider

        for provider in [
            OllamaProvider(),
            GroqProvider(),
            OpenAIProvider(),
            AnthropicProvider(),
            OpenRouterProvider(),
            KokoroProvider(),
            PiperProvider(),
            ElevenLabsProvider(),
            DuckDuckGoProvider(),
            TavilyProvider(),
            BraveProvider(),
            PillowProvider(),
        ]:
            self.providers.register(provider)

    def _register_tools(self) -> None:
        # Playwright browser
        try:
            from providers.scraper.playwright import PlaywrightBrowser
            self.capabilities.register_tool(Capability.BROWSER, PlaywrightBrowser())
            self.capabilities.register_tool(Capability.WEB_SCRAPING, PlaywrightBrowser())
        except Exception:
            pass

        # ffmpeg / moviepy for video assembly
        try:
            from providers.video.ffmpeg import FFmpegAssembler
            self.capabilities.register_tool(Capability.VIDEO_ASSEMBLY, FFmpegAssembler())
        except Exception:
            pass


# ─── Module-level singleton ────────────────────────────────────
runtime = Runtime()
