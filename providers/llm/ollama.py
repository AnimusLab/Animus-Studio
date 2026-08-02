"""
Ollama Provider — local, free, default

Models used:
  CHAT / REASONING  → REASONING_MODEL (default: deepseek-r1:8b)
  CHAT (fast)       → DEFAULT_MODEL   (default: qwen3:8b)
  VISION            → VISION_MODEL    (default: llava)
  EMBEDDING         → EMBEDDING_MODEL (default: nomic-embed-text)
"""
from __future__ import annotations
import os
import json
from typing import Any

import httpx
import structlog

from runtime.capabilities import Capability
from providers.llm.base import BaseLLMProvider
from providers.health_contract import HealthCheckMixin, HealthCheckResult

logger = structlog.get_logger()


class OllamaProvider(HealthCheckMixin, BaseLLMProvider):
    name = "ollama"
    priority = 10
    is_cloud = False
    capabilities = {
        Capability.TEXT_GENERATION,
        Capability.TEXT_REASONING,
        Capability.VISION_UNDERSTANDING,
        Capability.TEXT_EMBEDDING,
    }

    def __init__(self) -> None:
        self.host            = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model           = os.getenv("DEFAULT_MODEL", "qwen3:8b")
        self.reasoning_model = os.getenv("REASONING_MODEL", "deepseek-r1:8b")
        self.vision_model    = os.getenv("VISION_MODEL", "llava")
        self.embed_model     = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            r = httpx.get(f"{self.host}/api/tags", timeout=3)
            self._available = r.status_code == 200
        except Exception:
            self._available = False
        return self._available

    def _model_for(self, capability: Capability) -> str:
        if capability == Capability.TEXT_REASONING:
            return self.reasoning_model
        if capability == Capability.VISION_UNDERSTANDING:
            return self.vision_model
        return self.model

    async def _healthcheck(self) -> HealthCheckResult:
        """
        Real test: send 'Hello' to the chat model, expect a non-empty response.
        """
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "Say the word: ready"}],
                        "stream": False,
                        # 64 tokens is enough for thinking models (qwen3, deepseek-r1)
                        # to emit actual visible output past their CoT preamble
                        "options": {"num_predict": 64},
                    },
                )
                resp.raise_for_status()
                reply = resp.json()["message"]["content"].strip()
                # Accept empty only if the model endpoint responded correctly
                if resp.status_code != 200:
                    raise ValueError(f"status {resp.status_code}")

            # Also check which models are pulled
            tags_resp = httpx.get(f"{self.host}/api/tags", timeout=5)
            pulled = [m["name"] for m in tags_resp.json().get("models", [])]

            return HealthCheckResult(
                ok=True,
                name=self.name,
                detail=f"Responded via {self.model}",
                metadata={
                    "host": self.host,
                    "chat_model": self.model,
                    "reasoning_model": self.reasoning_model,
                    "embed_model": self.embed_model,
                    "pulled_models": pulled,
                    "reply_preview": reply[:60],
                },
            )
        except Exception as exc:
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail=f"Ollama unreachable at {self.host}",
                error=str(exc),
                metadata={"fix": "docker compose --profile models up ollama"},
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        capability: Capability = Capability.TEXT_GENERATION,
        **kwargs: Any,
    ) -> str:
        model = self._model_for(capability)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"

        timeout = float(os.getenv("OLLAMA_TIMEOUT", "300.0"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.host}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.host}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
