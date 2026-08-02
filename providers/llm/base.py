"""
Base LLM Provider
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from runtime.capabilities import Capability



class BaseLLMProvider(ABC):
    name: str = "base_llm"
    priority: int = 100
    is_cloud: bool = False
    capabilities: set[Capability] = set()
    model: str = ""


    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> str: ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict:
        import json
        raw = await self.chat(messages, json_mode=True, **kwargs)
        raw = raw.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(raw)
