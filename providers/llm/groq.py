"""Groq Provider — fast, free tier, optional"""
from __future__ import annotations
import os
from typing import Any
from runtime.capabilities import Capability
from providers.llm.base import BaseLLMProvider



class GroqProvider(BaseLLMProvider):
    name = "groq"
    priority = 20
    is_cloud = True
    capabilities = {Capability.TEXT_GENERATION, Capability.TEXT_REASONING}
    model = "llama-3.3-70b-versatile"


    def __init__(self) -> None:
        self._key = os.getenv("GROQ_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._key and self._key.startswith("gsk_"))

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        import litellm
        extra: dict[str, Any] = {}
        if json_mode:
            extra["response_format"] = {"type": "json_object"}
        resp = await litellm.acompletion(
            model=f"groq/{self.model}",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self._key,
            **extra,
        )
        return resp.choices[0].message.content

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Groq does not provide embeddings")
