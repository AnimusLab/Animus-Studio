"""Base Voice Provider"""
from __future__ import annotations
from abc import ABC, abstractmethod
from runtime.capabilities import Capability


class BaseVoiceProvider(ABC):
    name: str = "base_voice"
    priority: int = 100
    capabilities = {Capability.VOICE_SYNTHESIS}
    model: str = ""

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> str:
        """Synthesize text to audio file. Returns output_path."""
        ...
