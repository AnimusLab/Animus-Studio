"""
agents/editor/agent.py

Editor Agent v2 — Department: Production

Renders 1080p video MP4 assemblies with:
  1. Dark mode background canvas (#0b0f19)
  2. Neon cyan animated progress bar (#00f0ff)
  3. Safe-margin top header section banners (y=90, zero clipping)
  4. Centered intro title card (y=360-440, zero clipping)
  5. Dynamic Screen Activity (Terminal logs, Architecture diagrams, Code blocks, Telemetry cards)
  6. Optional closed captions / subtitles (burn_subtitles=False by default)
"""
from __future__ import annotations

import os
import re
import textwrap
from pathlib import Path
from typing import Any

import structlog
from agents.base import BaseAgent, AgentContext
from agents.editor.visuals import (
    render_terminal_card,
    render_architecture_card,
    render_code_card,
    render_metric_card,
)

logger = structlog.get_logger()
OUTPUT_DIR = Path("outputs")


def _resolve_font(font_name: str = "Arial") -> str | None:
    win_fonts = r"C:\Windows\Fonts"
    if os.path.exists(win_fonts):
        if "Bold" in font_name:
            f = os.path.join(win_fonts, "arialbd.ttf")
        else:
            f = os.path.join(win_fonts, "arial.ttf")
        if os.path.exists(f):
            return f
    return None


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))
    return (11, 15, 25)


def _set_pos(clip: Any, pos: Any) -> Any:
    if hasattr(clip, "with_position"):
        return clip.with_position(pos)
    elif hasattr(clip, "set_position"):
        return clip.set_position(pos)
    return clip


def _set_dur(clip: Any, dur: float) -> Any:
    if hasattr(clip, "with_duration"):
        return clip.with_duration(dur)
    elif hasattr(clip, "set_duration"):
        return clip.set_duration(dur)
    return clip


def _set_start(clip: Any, start: float) -> Any:
    if hasattr(clip, "with_start"):
        return clip.with_start(start)
    elif hasattr(clip, "set_start"):
        return clip.set_start(start)
    return clip


def _set_audio(video: Any, audio: Any) -> Any:
    if hasattr(video, "with_audio"):
        return video.with_audio(audio)
    elif hasattr(video, "set_audio"):
        return video.set_audio(audio)
    return video


def _set_opacity(clip: Any, opacity: float) -> Any:
    if hasattr(clip, "with_opacity"):
        return clip.with_opacity(opacity)
    elif hasattr(clip, "set_opacity"):
        return clip.set_opacity(opacity)
    return clip


class EditorAgent(BaseAgent):
    name = "editor"
    department = "production"
    produces = {"video_path"}

    async def _run(self, rt_or_ctx: Any, spec_or_input: Any, exec_or_none: Any = None) -> dict[str, Any]:
        if exec_or_none is not None:
            exec_ctx = exec_or_none
            script = exec_ctx.get("script", {})
            brand = exec_ctx.get("brand", {})
            audio_path = exec_ctx.get("audio_path", "")
            job_id = exec_ctx.execution_id
        else:
            context = rt_or_ctx
            input_data = spec_or_input or {}
            script = context.get("script", input_data.get("script", {}))
            brand = getattr(context, "brand", {}) or input_data.get("brand", {})
            audio_path = context.get("audio_path", input_data.get("audio_path", ""))
            job_id = getattr(context, "job_id", f"job_{int(os.times().system * 100)}")

        self._log.info("editor.v2.assembling", job_id=job_id, audio=audio_path)

        out_dir = OUTPUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str((out_dir / "final.mp4").resolve())

        if not audio_path or not os.path.exists(audio_path):
            self._log.warning("editor.v2.missing_audio", path=audio_path)
            return {"video_path": "", "duration": 0.0}

        burn_subtitles = input_data.get("burn_subtitles", False)

        result = self._render_video_v2(
            audio_path=audio_path,
            script=script,
            brand=brand,
            output_path=output_path,
            job_id=job_id,
            burn_subtitles=burn_subtitles,
        )

        if hasattr(rt_or_ctx, "set"):
            rt_or_ctx.set("video_path", result["video_path"])

        return result

    def _render_video_v2(
        self,
        audio_path: str,
        script: dict[str, Any],
        brand: dict[str, Any],
        output_path: str,
        job_id: str,
        burn_subtitles: bool = False,
    ) -> dict[str, Any]:
        try:
            from moviepy import (
                AudioFileClip,
                ColorClip,
                CompositeVideoClip,
                ImageClip,
                TextClip,
                VideoClip,
            )
        except ImportError:
            from moviepy.editor import (
                AudioFileClip,
                ColorClip,
                CompositeVideoClip,
                ImageClip,
                TextClip,
                VideoClip,
            )

        # ── 1. Load audio & setup 1080p canvas ──────────────────────
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        W, H = 1920, 1080
        fps = 24

        font_regular = _resolve_font(brand.get("font", "Arial"))
        font_bold = _resolve_font(brand.get("font", "Arial-Bold"))

        # ── 2. Background Canvas (#0b0f19 dark mode) ──────────────
        bg_color = _hex_to_rgb(brand.get("primary_color", "#0b0f19"))
        background = _set_dur(ColorClip(size=(W, H), color=bg_color), duration)

        # ── 3. Animated Progress Bar (Cyan #00f0ff) ───────────────
        def make_progress_frame(t: float):
            import numpy as np
            img = np.zeros((10, W, 3), dtype=np.uint8)
            progress_w = int((t / max(duration, 0.1)) * W)
            if progress_w > 0:
                img[:, :progress_w, :] = [0, 240, 255]
            return img

        progress_bar = _set_pos(_set_dur(VideoClip(frame_function=make_progress_frame), duration), ("left", H - 10))

        # ── 4. Title Intro Card (y=360-440 with safe margins) ─────
        title = script.get("title", "Animus Studio Production")
        title_clip = _set_dur(_set_pos(
            TextClip(
                text=textwrap.fill(title, 32),
                font_size=60,
                color="white",
                font=font_bold,
            ),
            ("center", 420)
        ), 3.5)

        brand_badge = _set_dur(_set_pos(
            TextClip(
                text=f"// {brand.get('name', 'ANIMUSLAB ENGINEERING').upper()}",
                font_size=26,
                color="#00f0ff",
                font=font_bold,
            ),
            ("center", 350)
        ), 3.5)

        if hasattr(title_clip, "crossfadein"):
            title_clip = title_clip.crossfadein(0.4).crossfadeout(0.4)
            brand_badge = brand_badge.crossfadein(0.4).crossfadeout(0.4)

        # ── 5. Safe Section Header Banners (y=90, zero clipping) ─
        section_clips = _build_section_headers(
            sections=script.get("sections", []),
            duration=duration,
            w=W,
            font=font_bold,
        )

        # ── 6. Dynamic Screen Activity Visual Cards (Terminal, Architecture, Code, Metrics) ───
        visual_card_clips = _build_dynamic_visual_clips(
            sections=script.get("sections", []),
            duration=duration,
            w=W,
            job_id=job_id,
        )

        # ── 7. Subtitle Captions (Optional) ───────────────────────
        subtitle_clips = []
        if burn_subtitles:
            subtitle_clips = _build_subtitle_clips(
                text=script.get("script", script.get("body", "")),
                duration=duration,
                width=W,
                color="white",
                font=font_regular,
            )

        # ── 8. Top Right Watermark (y=130, safe margin) ───────────
        watermark_clip = _set_dur(_set_pos(_set_opacity(
            TextClip(
                text="ANIMUS STUDIO",
                font_size=24,
                color="#00f0ff",
                font=font_bold,
            ),
            0.6
        ), (W - 280, 130)), duration)

        # ── 9. Composite Layers ───────────────────────────────────
        layers = [
            background,
            progress_bar,
            brand_badge,
            title_clip,
            *section_clips,
            *visual_card_clips,
            *subtitle_clips,
            watermark_clip,
        ]
        video = _set_audio(CompositeVideoClip(layers, size=(W, H)), audio)

        # ── 10. Render Final MP4 (High Quality 1080p) ────────────
        video.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            bitrate="8000k",
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
    """Renders top section headers placed safely at y=130 (no top clipping)."""
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
            (100, 130)
        ), start_t), max(slice_dur, 0.5))

        if hasattr(header_clip, "crossfadein"):
            header_clip = header_clip.crossfadein(0.3).crossfadeout(0.3)

        clips.append(header_clip)

    return clips


def _build_dynamic_visual_clips(
    sections: list[dict[str, Any]],
    duration: float,
    w: int,
    job_id: str,
) -> list:
    """Renders dynamic high-context visual cards centered on screen for each section topic."""
    try:
        from moviepy import ImageClip
    except ImportError:
        from moviepy.editor import ImageClip

    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    n = max(len(sections), 1)
    slice_dur = (duration - 3.5) / n
    clips = []

    card_renderers = [
        ("terminal.png", render_terminal_card),
        ("architecture.png", lambda p, heading="": render_architecture_card(p)),
        ("code.png", lambda p, heading="": render_code_card(p)),
        ("metric.png", lambda p, heading="": render_metric_card(p)),
    ]

    for idx in range(n):
        card_name, render_fn = card_renderers[idx % len(card_renderers)]
        img_path = str(out_dir / card_name)
        heading = sections[idx].get("heading", f"Section {idx + 1}") if sections else "Production System"

        try:
            if card_name == "terminal.png":
                render_fn(img_path, heading)
            else:
                render_fn(img_path)

            start_t = 3.5 + (idx * slice_dur)
            dur = max(slice_dur - 0.2, 0.5)

            card_clip = _set_dur(_set_start(_set_pos(
                ImageClip(img_path),
                ("center", 240)
            ), start_t), dur)

            if hasattr(card_clip, "crossfadein"):
                card_clip = card_clip.crossfadein(0.3).crossfadeout(0.3)

            clips.append(card_clip)
        except Exception as err:
            logger.warning("visuals.card_render_failed", card=card_name, error=str(err))

    return clips


def _build_subtitle_clips(
    text: str,
    duration: float,
    width: int,
    color: str,
    font: str | None,
) -> list:
    """Renders optional bottom subtitles."""
    try:
        from moviepy import TextClip
    except ImportError:
        from moviepy.editor import TextClip

    clean_text = re.sub(r"\[.*?\]|\(.*?\)", "", text).strip()
    words = clean_text.split()
    if not words:
        return []

    chunk_size = 7
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
    chunk_dur = duration / max(len(chunks), 1)

    clips = []
    for i, chunk in enumerate(chunks):
        start_t = i * chunk_dur
        txt_clip = _set_dur(_set_start(_set_pos(
            TextClip(
                text=chunk,
                font_size=36,
                color=color,
                font=font,
            ),
            ("center", 900)
        ), start_t), max(chunk_dur - 0.1, 0.4))
        clips.append(txt_clip)

    return clips
