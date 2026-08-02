"""
Kokoro TTS Provider — local, free, high quality

Package: pip install kokoro-onnx soundfile
Import:  from kokoro_onnx import Kokoro   (not `kokoro`)

Voices: af_heart (default), af_bella, am_adam, bf_emma, bm_george, ...
"""
from __future__ import annotations
import os
from pathlib import Path
from providers.voice.base import BaseVoiceProvider
from providers.health_contract import HealthCheckMixin, HealthCheckResult


class KokoroProvider(HealthCheckMixin, BaseVoiceProvider):
    name = "kokoro"
    priority = 10
    model = "kokoro-onnx"

    def __init__(self) -> None:
        self._voice = os.getenv("KOKORO_VOICE", "af_heart")
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from kokoro_onnx import Kokoro  # noqa: F401
            import soundfile  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False
        return self._available

    def _locate_weights(self) -> tuple[str, str]:
        candidates = [
            ("models/kokoro/kokoro-v1.0.onnx", "models/kokoro/voices-v1.0.bin"),
            ("kokoro-v1.0.onnx", "voices-v1.0.bin"),
        ]
        for model_path, voices_path in candidates:
            if Path(model_path).exists() and Path(voices_path).exists():
                return model_path, voices_path
        return "models/kokoro/kokoro-v1.0.onnx", "models/kokoro/voices-v1.0.bin"

    async def _healthcheck(self) -> HealthCheckResult:
        """
        Real test: synthesize the phrase 'Studio ready.' and verify the output
        audio file has non-zero length.
        """
        if not self.is_available():
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="Package missing (kokoro-onnx or soundfile)",
                error="ImportError on kokoro_onnx or soundfile",
                metadata={"fix": "pip install kokoro-onnx soundfile"},
            )

        model_path, voices_path = self._locate_weights()
        if not Path(model_path).exists() or not Path(voices_path).exists():
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="Kokoro weights missing",
                error=f"Model files not found at {model_path} or {voices_path}",
                metadata={"fix": "Download kokoro-v1.0.onnx & voices-v1.0.bin into models/kokoro/"},
            )

        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            await self.synthesize("Studio ready.", tmp_path, voice=self._voice)

            size = Path(tmp_path).stat().st_size
            Path(tmp_path).unlink(missing_ok=True)

            if size < 100:
                raise ValueError(f"Audio file suspiciously small: {size} bytes")

            return HealthCheckResult(
                ok=True,
                name=self.name,
                detail=f"Synthesized test phrase ({size // 1024}KB)",
                metadata={"voice": self._voice, "output_bytes": size},
            )
        except Exception as exc:
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="Synthesis failed",
                error=str(exc),
            )

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> str:
        import asyncio
        import soundfile as sf
        from kokoro_onnx import Kokoro

        voice = voice or self._voice
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        model_path, voices_path = self._locate_weights()

        def _run() -> None:
            kokoro = Kokoro(model_path, voices_path)
            samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
            sf.write(output_path, samples, sample_rate)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run)
        return output_path
