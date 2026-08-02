"""
Voice Agent — Department: Production

Capabilities required:
  - VOICE_SYNTHESIS (text-to-speech)

Resolution order (automatic via ProviderRegistry):
  Kokoro → Piper → ElevenLabs

The agent never knows or cares which provider ran.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from agents.base import BaseAgent
from runtime.capabilities import Capability


class VoiceAgent(BaseAgent):
    name       = "voice"
    department = "production"
    requires   = {Capability.VOICE_SYNTHESIS}
    produces   = {"audio_path"}

    async def _run(self, rt_or_ctx: Any, spec_or_input: Any, exec_or_none: Any = None) -> dict[str, Any]:
        if exec_or_none is not None:
            exec_ctx = exec_or_none
            script = exec_ctx.get("script", {})
            job_id = exec_ctx.execution_id
            voice_id = getattr(spec_or_input, "brand", {}).get("voice_id") if hasattr(spec_or_input, "brand") else None
        else:
            context = rt_or_ctx
            script = context.get("script", {})
            job_id = getattr(context, "job_id", "job_default")
            brand = getattr(context, "brand", {}) or {}
            voice_id = brand.get("voice_id")

        text = script.get("script") or script.get("body", "")
        if not text:
            self._log.error("voice.no_text")
            return {"error": "No script text found"}

        self._log.info("voice.synthesizing", chars=len(text), job_id=job_id)

        out_dir = Path("outputs") / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        audio_path = str(out_dir / "voice.mp3")

        # Resolve TTS provider — Kokoro, Piper, or ElevenLabs
        tts = self.resolve(rt_or_ctx, Capability.VOICE_SYNTHESIS)

        await tts.synthesize(text, audio_path, voice=voice_id)

        self._log.info(
            "voice.done",
            provider=type(tts).__name__,
            output=audio_path,
        )

        if hasattr(rt_or_ctx, "set"):
            rt_or_ctx.set("audio_path", audio_path)

        return {"audio_path": audio_path}
