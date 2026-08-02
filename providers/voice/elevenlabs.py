"""ElevenLabs TTS Provider — optional cloud upgrade"""
from __future__ import annotations
import os
from pathlib import Path
from providers.voice.base import BaseVoiceProvider


class ElevenLabsProvider(BaseVoiceProvider):
    name = "elevenlabs"
    priority = 30
    model = "elevenlabs"


    def __init__(self) -> None:
        self._key     = os.getenv("ELEVENLABS_API_KEY", "")
        self._voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")

    def is_available(self) -> bool:
        return bool(self._key and self._voice_id)

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> str:
        import httpx
        voice_id = voice or self._voice_id
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": self._key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            Path(output_path).write_bytes(resp.content)

        return output_path
