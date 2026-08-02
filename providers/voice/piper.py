"""
Piper TTS Provider — local, free, fast

Requires: pip install piper-tts
Models: en_US-lessac-medium (default)

Fallback when Kokoro is unavailable.
"""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from providers.voice.base import BaseVoiceProvider


class PiperProvider(BaseVoiceProvider):
    name = "piper"
    priority = 20
    model = "piper"


    def __init__(self) -> None:
        self._model_name = os.getenv("PIPER_MODEL", "en_US-lessac-medium")
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            result = subprocess.run(
                ["piper", "--help"], capture_output=True, timeout=5
            )
            self._available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._available = False
        return self._available

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> str:
        import asyncio

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        model = voice or self._model_name

        proc = await asyncio.create_subprocess_exec(
            "piper",
            "--model", model,
            "--output_file", output_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate(input=text.encode())
        return output_path
