"""OpenAI Provider — optional cloud upgrade"""
from __future__ import annotations
import os
from typing import Any
from runtime.capabilities import Capability
from providers.llm.base import BaseLLMProvider



class OpenAIProvider(BaseLLMProvider):
    name = "openai"
    priority = 30
    is_cloud = True
    capabilities = {
        Capability.TEXT_GENERATION,
        Capability.TEXT_REASONING,
        Capability.VISION_UNDERSTANDING,
        Capability.TEXT_EMBEDDING,
    }
    model = "gpt-4o"


    def __init__(self) -> None:
        self._key = os.getenv("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._key and self._key.startswith("sk-"))

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        import litellm
        kwargs_final: dict[str, Any] = {}
        if json_mode:
            kwargs_final["response_format"] = {"type": "json_object"}
        resp = await litellm.acompletion(
            model=f"openai/{self.model}",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self._key,
            **kwargs_final,
        )
        return resp.choices[0].message.content

    async def embed(self, text: str) -> list[float]:
        import litellm
        resp = await litellm.aembedding(
            model="openai/text-embedding-3-small",
            input=text,
            api_key=self._key,
        )
        return resp.data[0]["embedding"]
