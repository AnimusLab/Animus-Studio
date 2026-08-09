"""
agents/editor/agent.py

Editor Agent v3 — Cinematic Video Engine

Renders 1080p video MP4 assemblies with:
  1. ANIMATED video backgrounds (procedural motion or Pexels stock footage)
     - No more static images / poster-wallpaper backgrounds
     - terminal_crash, network_topology, code_stream, particle_vortex per section
  2. Broadcast-style Lower-Third HUD overlays (≤18% of frame)
     - Background is FULLY visible for 82%+ of every frame
  3. Cross-dissolve transitions between sections (0.4s fade)
  4. Ken Burns slow-zoom simulation via progressive ffmpeg crop
  5. 2.39:1 Widescreen Letterbox Scope Framing
  6. Animated cyan progress bar
  7. Optional closed captions (burn_subtitles=False by default)

Path A (Pexels): Set PEXELS_API_KEY in .env → real stock footage with people/action
Path B (Procedural): No API key needed → animated motion backgrounds auto-render
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
    render_padded_text_png,
    render_lower_third,
    render_corner_metric,
)
from agents.editor.stock_footage import get_stock_bg_clip
from agents.editor.cinematic import render_letterbox_overlay

logger = structlog.get_logger()
OUTPUT_DIR = Path("outputs")

# Section style mapping (determines which animation type each section gets)
_SECTION_STYLES = ["server_alert", "architecture_blue", "code_matrix", "audit_emerald"]

# Lower-third accent colours per section
_SECTION_ACCENTS = ["#ff3333", "#00ccff", "#00ff88", "#ffcc00"]

# Corner metric badges per section (value, label, accent)
_SECTION_METRICS = [
    ("847", "Silent Failures/Day",  "#ff3333"),
    ("0%",  "State Drift",          "#00ccff"),
    ("100%","Audit Traceability",   "#00ff88"),
    ("∞",   "Replay Integrity",     "#ffcc00"),
]


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

        self._log.info("editor.v3.assembling", job_id=job_id, audio=audio_path)

        out_dir = OUTPUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str((out_dir / "final.mp4").resolve())

        if not audio_path or not os.path.exists(audio_path):
            self._log.warning("editor.v3.missing_audio", path=audio_path)
            return {"video_path": "", "duration": 0.0}

        burn_subtitles = (spec_or_input or {}).get("burn_subtitles", False)

        result = self._render_video_v3(
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

    def _render_video_v3(
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
                VideoFileClip,
                CompositeVideoClip,
                ImageClip,
                VideoClip,
                concatenate_videoclips,
            )
        except ImportError:
            from moviepy.editor import (
                AudioFileClip,
                VideoFileClip,
                CompositeVideoClip,
                ImageClip,
                VideoClip,
                concatenate_videoclips,
            )

        out_dir = OUTPUT_DIR / job_id

        # ── 1. Audio ─────────────────────────────────────────────────
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        W, H = 1920, 1080
        fps = 24

        title = script.get("title", "Animus Studio Production").replace("Reliabilitv", "Reliability")
        sections = script.get("sections", [])
        n_sections = max(len(sections), 1)

        # ── 2. Animated Video Backgrounds (Path A: Pexels / Path B: Procedural) ──
        self._log.info("editor.v3.rendering_animated_backgrounds", n_sections=n_sections)
        bg_clips = _build_animated_bg_clips(
            sections=sections,
            duration=duration,
            out_dir=out_dir,
        )

        # ── 3. Animated Progress Bar ──────────────────────────────────
        def make_progress_frame(t: float):
            import numpy as np
            img = __import__("numpy").zeros((10, W, 3), dtype=__import__("numpy").uint8)
            pw = int((t / max(duration, 0.1)) * W)
            if pw > 0:
                img[:, :pw, :] = [0, 240, 255]
            return img

        import numpy as np
        progress_bar = _set_pos(
            _set_dur(VideoClip(frame_function=make_progress_frame), duration),
            ("left", H - 10),
        )

        # ── 4. Intro Title (first 3.5s — full screen atmospheric, no card) ───
        title_png = render_padded_text_png(
            str(out_dir / "title_intro.png"),
            textwrap.fill(title, 32),
            font_size=58,
            color="white",
            bold=True,
        )
        badge_png = render_padded_text_png(
            str(out_dir / "brand_badge.png"),
            f"// {brand.get('name', 'ANIMUSLAB ENGINEERING').upper()}",
            font_size=28,
            color="#00f0ff",
            bold=True,
        )
        title_clip = _set_dur(_set_pos(ImageClip(title_png), ("center", 440)), 3.5)
        brand_badge = _set_dur(_set_pos(ImageClip(badge_png), ("center", 370)), 3.5)
        if hasattr(title_clip, "crossfadein"):
            title_clip = title_clip.crossfadein(0.5).crossfadeout(0.5)
            brand_badge = brand_badge.crossfadein(0.5).crossfadeout(0.5)

        # ── 5. Lower-Third HUD Overlays (replaces opaque cards) ──────
        self._log.info("editor.v3.rendering_lower_thirds")
        lower_third_clips = _build_lower_third_clips(
            sections=sections,
            duration=duration,
            out_dir=out_dir,
        )

        # ── 6. Corner Metric Badges ───────────────────────────────────
        corner_badge_clips = _build_corner_badge_clips(
            sections=sections,
            duration=duration,
            out_dir=out_dir,
        )

        # ── 7. 2.39:1 Letterbox Scope ─────────────────────────────────
        letterbox_png = render_letterbox_overlay(str(out_dir / "letterbox_scope.png"))
        letterbox_clip = _set_dur(ImageClip(letterbox_png), duration)

        # ── 8. Composite All Layers ────────────────────────────────────
        layers = [
            *bg_clips,          # Animated full-screen backgrounds (fills ~82%+ of frame)
            progress_bar,       # Thin cyan bar at very bottom
            brand_badge,        # Intro badge
            title_clip,         # Intro title (atmospheric, no box)
            *lower_third_clips, # Broadcast lower-thirds (≤18% of frame)
            *corner_badge_clips,# Small corner metrics
            letterbox_clip,     # 2.39:1 scope bars
        ]
        video = _set_audio(CompositeVideoClip(layers, size=(W, H)), audio)

        # ── 9. Render Final MP4 ────────────────────────────────────────
        self._log.info("editor.v3.writing_final_mp4", output=output_path)
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

def _build_animated_bg_clips(
    sections: list[dict[str, Any]],
    duration: float,
    out_dir: Path,
) -> list:
    """
    Builds animated video background clips for each section.
    Tries Pexels stock footage first (Path A), falls back to procedural (Path B).
    Returns a list of VideoFileClip objects positioned as full-screen backgrounds.
    """
    try:
        from moviepy import VideoFileClip
    except ImportError:
        from moviepy.editor import VideoFileClip

    n = max(len(sections), 1)
    section_dur = duration / n
    clips = []

    for idx in range(n):
        style = _SECTION_STYLES[idx % len(_SECTION_STYLES)]
        start_t = idx * section_dur
        seg_dur = section_dur

        out_path = str(out_dir / f"bg_animated_{idx + 1}.mp4")

        logger.info(
            "editor.v3.bg_rendering",
            section=idx + 1,
            style=style,
            duration=round(seg_dur, 2),
        )

        try:
            clip_path, source = get_stock_bg_clip(
                section_type=style,
                duration=seg_dur,
                output_path=out_path,
            )
            logger.info("editor.v3.bg_ready", section=idx + 1, source=source, path=clip_path)

            bg_clip = VideoFileClip(clip_path, audio=False)
            bg_clip = _set_dur(bg_clip, seg_dur)
            bg_clip = _set_start(bg_clip, start_t)

            # Cross-dissolve in (except first section)
            if idx > 0 and hasattr(bg_clip, "crossfadein"):
                bg_clip = bg_clip.crossfadein(0.4)

            clips.append(bg_clip)

        except Exception as err:
            logger.warning("editor.v3.bg_failed", section=idx + 1, error=str(err))
            # Emergency fallback: solid color
            try:
                from moviepy import ColorClip
            except ImportError:
                from moviepy.editor import ColorClip
            clips.append(_set_dur(_set_start(ColorClip((1920, 1080), color=(5, 8, 15)), start_t), seg_dur))

    return clips


def _build_lower_third_clips(
    sections: list[dict[str, Any]],
    duration: float,
    out_dir: Path,
) -> list:
    """
    Renders broadcast lower-third HUD strips for each section.
    Each strip appears ~0.5s after section starts, fades out before next section.
    Covers ≤18% of frame height — background is fully visible above.
    """
    try:
        from moviepy import ImageClip
    except ImportError:
        from moviepy.editor import ImageClip

    if not sections:
        return []

    n = len(sections)
    section_dur = (duration - 3.5) / max(n, 1)
    clips = []

    for idx, sec in enumerate(sections):
        heading = sec.get("heading", f"Section {idx + 1}")
        title_str = f"SECTION {idx + 1:02d}  //  {heading.upper()}"

        # Subtitle: first sentence of content (up to ~70 chars)
        content = sec.get("content", sec.get("narration", ""))
        subtitle = content[:70].rsplit(" ", 1)[0] + "…" if len(content) > 70 else content

        accent = _SECTION_ACCENTS[idx % len(_SECTION_ACCENTS)]
        png_path = str(out_dir / f"lower_third_{idx + 1}.png")

        render_lower_third(
            png_path,
            title=title_str,
            subtitle=subtitle,
            accent_color=accent,
        )

        start_t = 3.5 + (idx * section_dur) + 0.5   # Slight delay after section start
        lt_dur = max(section_dur - 1.2, 2.0)         # Fade out before section end

        lt_clip = _set_dur(
            _set_start(ImageClip(png_path), start_t),
            lt_dur,
        )
        if hasattr(lt_clip, "crossfadein"):
            lt_clip = lt_clip.crossfadein(0.4).crossfadeout(0.4)

        clips.append(lt_clip)

    return clips


def _build_corner_badge_clips(
    sections: list[dict[str, Any]],
    duration: float,
    out_dir: Path,
) -> list:
    """
    Renders small corner metric badges that appear after lower-thirds settle.
    These give the viewer a data point relevant to each section (847 failures,
    0% drift, 100% audit, etc.) without covering the background.
    """
    try:
        from moviepy import ImageClip
    except ImportError:
        from moviepy.editor import ImageClip

    if not sections:
        return []

    n = len(sections)
    section_dur = (duration - 3.5) / max(n, 1)
    clips = []

    corners = ["tr", "tr", "tr", "tr"]  # Top-right for all sections

    for idx in range(min(n, len(_SECTION_METRICS))):
        value, label, accent = _SECTION_METRICS[idx]
        png_path = str(out_dir / f"corner_badge_{idx + 1}.png")

        render_corner_metric(
            png_path,
            value=value,
            label=label,
            accent_color=accent,
            corner=corners[idx % len(corners)],
        )

        start_t = 3.5 + (idx * section_dur) + 1.2   # Appears 1.2s into section
        badge_dur = max(section_dur - 2.0, 1.5)

        badge_clip = _set_dur(_set_start(ImageClip(png_path), start_t), badge_dur)
        if hasattr(badge_clip, "crossfadein"):
            badge_clip = badge_clip.crossfadein(0.5).crossfadeout(0.5)

        clips.append(badge_clip)

    return clips
