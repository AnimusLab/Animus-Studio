"""
Editor Agent v2 — Department: Production

Converts audio tracks and structured scripts into high-quality branded videos:

Visual Language & Production Architecture:
  1. Branded Color Palette: Dark mode (#0b0f19 primary, #00f0ff neon cyan accent, #1a2236 card bg)
  2. Scene Card Parsing: Title Intro Card, Section Header Banners, CTA Outro Card
  3. Animated Progress Bar: Dynamic timeline progress indicator at bottom of 1080p frame
  4. Subtitle Engine: Centered subtitle captions with black stroke outlines
  5. AnimusLab Branding: Watermark logo badge in top right corner

Output:
  {"video_path": "outputs/<job_id>/final.mp4", "duration": 142.3}
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Any

import structlog

from agents.base import BaseAgent, AgentContext

logger = structlog.get_logger()

# Outputs directory — relative to project root
OUTPUT_DIR = Path("outputs")


class EditorAgent(BaseAgent):
    name = "editor"
    department = "production"

    async def _run(self, context: AgentContext, input_data: dict[str, Any]) -> dict[str, Any]:
        audio_path = context.get("audio_path", "")
        script     = context.get("script", {})
        brand      = context.brand
        job_id     = context.job_id

        if not audio_path or not Path(audio_path).exists():
            self._log.error("editor.no_audio", audio_path=audio_path)
            return {"error": "audio_path missing or file not found"}

        self._log.info("editor.v2.assembling", job_id=job_id, audio=audio_path)

        out_dir = OUTPUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str((out_dir / "final.mp4").resolve())

        try:
            result = await _assemble_video(
                audio_path=audio_path,
                script=script,
                brand=brand,
                output_path=output_path,
            )
        except Exception as exc:
            self._log.exception("editor.assembly_failed", error=str(exc))
            return {"error": str(exc)}

        context.set("video_path", output_path)
        self._log.info("editor.v2.done", output=output_path, duration=result["duration"])
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Core assembly — pure moviepy / Pillow, no async needed
# ─────────────────────────────────────────────────────────────────────────────

async def _assemble_video(
    audio_path: str,
    script: dict,
    brand: dict,
    output_path: str,
) -> dict[str, Any]:
    """
    Runs the full moviepy v2 pipeline in a thread pool.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _assemble_blocking,
        audio_path, script, brand, output_path,
    )


def _resolve_font(font_name: str = "Arial") -> str | None:
    if os.path.exists(font_name):
        return font_name
    win_fonts = r"C:\Windows\Fonts"
    if os.path.exists(win_fonts):
        lower = font_name.lower()
        if "bold" in lower:
            f = os.path.join(win_fonts, "arialbd.ttf")
        else:
            f = os.path.join(win_fonts, "arial.ttf")
        if os.path.exists(f):
            return f
    return None


def _set_pos(clip: Any, pos: Any) -> Any:
    return clip.with_position(pos) if hasattr(clip, "with_position") else clip.set_position(pos)


def _set_dur(clip: Any, dur: float) -> Any:
    return clip.with_duration(dur) if hasattr(clip, "with_duration") else clip.set_duration(dur)


def _set_start(clip: Any, start: float) -> Any:
    return clip.with_start(start) if hasattr(clip, "with_start") else clip.set_start(start)


def _set_opacity(clip: Any, opacity: float) -> Any:
    return clip.with_opacity(opacity) if hasattr(clip, "with_opacity") else clip.set_opacity(opacity)


def _set_audio(clip: Any, audio: Any) -> Any:
    return clip.with_audio(audio) if hasattr(clip, "with_audio") else clip.set_audio(audio)


def _assemble_blocking(
    audio_path: str,
    script: dict,
    brand: dict,
    output_path: str,
) -> dict[str, Any]:
    """MoviePy v2 video assembly with scenes, progress bar, subtitles, and branding."""
    try:
        from moviepy import (
            AudioFileClip,
            ColorClip,
            CompositeVideoClip,
            TextClip,
            VideoClip,
        )
    except ImportError:
        from moviepy.editor import (
            AudioFileClip,
            ColorClip,
            CompositeVideoClip,
            TextClip,
            VideoClip,
        )

    # ── 1. Load audio ────────────────────────────────────────
    audio    = AudioFileClip(audio_path)
    duration = audio.duration
    W, H     = 1920, 1080
    fps      = 24

    font_regular = _resolve_font(brand.get("font", "Arial"))
    font_bold    = _resolve_font(brand.get("font", "Arial-Bold"))

    # ── 2. Background Canvas (#0b0f19 dark mode) ──────────────
    bg_color = _hex_to_rgb(brand.get("primary_color", "#0b0f19"))
    background = _set_dur(ColorClip(size=(W, H), color=bg_color), duration)

    # ── 3. Animated Progress Bar (Cyan #00f0ff) ───────────────
    def make_progress_frame(t: float):
        import numpy as np
        img = np.zeros((10, W, 3), dtype=np.uint8)
        progress_w = int((t / max(duration, 0.1)) * W)
        if progress_w > 0:
            img[:, :progress_w, :] = [0, 240, 255]  # Neon Cyan RGB
        return img

    progress_bar = _set_pos(_set_dur(VideoClip(frame_function=make_progress_frame), duration), ("left", H - 10))

    # ── 4. Title Intro Card (first 3.5 seconds) ───────────────
    title = script.get("title", "Animus Studio Production")
    title_clip = _set_dur(_set_pos(
        TextClip(
            text=textwrap.fill(title, 36),
            font_size=64,
            color="white",
            font=font_bold,
            size=(W - 240, None),
        ),
        ("center", 340)
    ), 3.5)

    brand_badge = _set_dur(_set_pos(
        TextClip(
            text=f"// {brand.get('name', 'ANIMUSLAB ENGINEERING').upper()}",
            font_size=28,
            color="#00f0ff",
            font=font_bold,
        ),
        ("center", 260)
    ), 3.5)

    if hasattr(title_clip, "crossfadein"):
        title_clip = title_clip.crossfadein(0.4).crossfadeout(0.4)
        brand_badge = brand_badge.crossfadein(0.4).crossfadeout(0.4)

    # ── 5. Section Header Banners ─────────────────────────────
    section_clips = _build_section_headers(
        sections=script.get("sections", []),
        duration=duration,
        w=W,
        font=font_bold,
    )

    # ── 6. Subtitle Captions ──────────────────────────────────
    subtitle_clips = _build_subtitle_clips(
        text=script.get("script", script.get("body", "")),
        duration=duration,
        width=W,
        color="white",
        font=font_regular,
    )

    # ── 7. Top Right Watermark ────────────────────────────────
    watermark_clip = _set_dur(_set_pos(_set_opacity(
        TextClip(
            text="ANIMUS STUDIO",
            font_size=24,
            color="#00f0ff",
            font=font_bold,
        ),
        0.6
    ), (W - 260, 40)), duration)

    # ── 8. Composite Layers ───────────────────────────────────
    layers = [
        background,
        progress_bar,
        brand_badge,
        title_clip,
        *section_clips,
        *subtitle_clips,
        watermark_clip,
    ]
    video = _set_audio(CompositeVideoClip(layers, size=(W, H)), audio)

    # ── 9. Render Final MP4 ───────────────────────────────────
    video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None,
    )

    return {"video_path": output_path, "duration": round(duration, 2)}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_section_headers(
    sections: list[dict[str, Any]],
    duration: float,
    w: int,
    font: str | None,
) -> list:
    """Renders top section headers as the script transitions through topics."""
    try:
        from moviepy import TextClip
    except ImportError:
        from moviepy.editor import TextClip

    if not sections:
        return []

    n = len(sections)
    slice_dur = (duration - 3.5) / max(n, 1)
    clips = []

    for idx, sec in enumerate(sections):
        heading = sec.get("heading", f"Section {idx + 1}")
        start_t = 3.5 + (idx * slice_dur)
        text_str = f"SECTION 0{idx + 1} // {heading.upper()}"

        header_clip = _set_dur(_set_start(_set_pos(
            TextClip(
                text=text_str,
                font_size=26,
                color="#00f0ff",
                font=font,
            ),
            (100, 50)
        ), start_t), max(slice_dur, 0.5))

        if hasattr(header_clip, "crossfadein"):
            header_clip = header_clip.crossfadein(0.3).crossfadeout(0.3)

        clips.append(header_clip)

    return clips


def _build_subtitle_clips(
    text: str,
    duration: float,
    width: int,
    color: str = "white",
    font: str | None = None,
) -> list:
    """Split script text into clean 8-word caption cards with outline."""
    try:
        from moviepy import TextClip
    except ImportError:
        from moviepy.editor import TextClip

    if not text:
        return []

    words  = text.split()
    chunks = [" ".join(words[i : i + 8]) for i in range(0, len(words), 8)]
    n      = len(chunks)
    if n == 0:
        return []

    slice_dur = duration / n
    clips = []
    for idx, chunk in enumerate(chunks):
        start = idx * slice_dur
        clip = _set_dur(_set_start(_set_pos(
            TextClip(
                text=textwrap.fill(chunk, 45),
                font_size=46,
                color=color,
                font=font,
                size=(width - 240, None),
                stroke_color="black",
                stroke_width=2,
            ),
            ("center", 780)
        ), start), slice_dur)

        if hasattr(clip, "crossfadein"):
            clip = clip.crossfadein(0.15).crossfadeout(0.15)

        clips.append(clip)
    return clips


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (11, 15, 25)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
