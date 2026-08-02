"""
providers/video/ffmpeg.py

FFmpegAssembler — VIDEO_ASSEMBLY capability.

Wraps moviepy (which uses ffmpeg internally).
Requires: pip install moviepy  +  ffmpeg on PATH
"""
from __future__ import annotations
import subprocess
from typing import Any
from providers.health_contract import HealthCheckMixin, HealthCheckResult


class FFmpegAssembler(HealthCheckMixin):
    """Video assembly via moviepy/ffmpeg."""

    name = "ffmpeg"
    model = "ffmpeg"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def _healthcheck(self) -> HealthCheckResult:
        """
        Real test: run 'ffmpeg -version' and parse the version string.
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg exited {result.returncode}")

            version_line = result.stdout.splitlines()[0] if result.stdout else "unknown"

            # Also verify moviepy is importable
            try:
                import moviepy  # noqa: F401
                moviepy_ok = True
            except ImportError:
                moviepy_ok = False

            return HealthCheckResult(
                ok=True,
                name=self.name,
                detail=f"FFmpeg available — {version_line[:60]}",
                metadata={
                    "version_line": version_line,
                    "moviepy_installed": moviepy_ok,
                },
            )
        except FileNotFoundError:
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="ffmpeg binary not found on PATH",
                error="FileNotFoundError: ffmpeg",
                metadata={"fix": "Install ffmpeg and add to PATH"},
            )
        except Exception as exc:
            return HealthCheckResult(
                ok=False,
                name=self.name,
                detail="ffmpeg check failed",
                error=str(exc),
            )

    async def assemble(
        self,
        audio_path: str,
        image_paths: list[str],
        output_path: str,
        duration_per_image: float = 5.0,
        fps: int = 24,
    ) -> str:
        """
        Assemble a video from audio + images.

        Args:
            audio_path:         Path to the audio file
            image_paths:        Ordered list of image paths
            output_path:        Where to write the final video
            duration_per_image: Seconds per image (ignored if audio drives timing)
            fps:                Frames per second

        Returns:
            output_path
        """
        import asyncio
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._assemble_blocking,
            audio_path,
            image_paths,
            output_path,
            duration_per_image,
            fps,
        )

    def _assemble_blocking(
        self,
        audio_path: str,
        image_paths: list[str],
        output_path: str,
        duration_per_image: float,
        fps: int,
    ) -> str:
        try:
            from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
        except ImportError:
            from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

        audio      = AudioFileClip(audio_path)
        total_dur  = audio.duration
        n_images   = len(image_paths) if image_paths else 1
        dur_each   = total_dur / n_images

        clips = []
        for img_path in image_paths:
            clip = ImageClip(img_path).set_duration(dur_each)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(audio)
        video.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        return output_path
