"""Anthropic Provider — optional cloud upgrade"""
from __future__ import annotations
import os
from typing import Any
from runtime.capabilities import Capability
from providers.llm.base import BaseLLMProvider



class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"
    priority = 40
    is_cloud = True
    capabilities = {Capability.TEXT_GENERATION, Capability.TEXT_REASONING}
    model = "claude-3-5-sonnet-20241022"


    def __init__(self) -> None:
        self._key = os.getenv("ANTHROPIC_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._key and self._key.startswith("sk-ant-"))

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        import litellm
        resp = await litellm.acompletion(
            model=f"anthropic/{self.model}",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self._key,
        )
        return resp.choices[0].message.content

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Anthropic does not provide embeddings")
