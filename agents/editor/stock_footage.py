"""
agents/editor/stock_footage.py

Path A: Pexels Stock Video Downloader.
Downloads real MP4 video clips (people, action, real-world visuals) from Pexels API.
Falls back to procedural motion backgrounds (motion_bg.py) if API key is unavailable.

Setup:
    Add PEXELS_API_KEY=your_key_here to d:\\Animus-Studio\\.env
    Free API key: https://www.pexels.com/api/ (2 minute signup)

Usage:
    path = get_stock_bg_clip(
        section_type="server_alert",
        duration=15.0,
        output_path="outputs/job_x/bg_s1.mp4",
    )
"""
from __future__ import annotations

import os
import subprocess
import urllib.request
import json
from pathlib import Path

import structlog

logger = structlog.get_logger()

# Pexels search queries per section style
_SECTION_QUERIES = {
    "server_alert":      [
        "server room engineer",
        "data center failure",
        "programmer typing terminal",
        "network operations center",
    ],
    "architecture_blue": [
        "data center engineer walking",
        "server room fiber optic",
        "network engineer cables",
        "technology infrastructure",
    ],
    "code_matrix":       [
        "programmer coding dark room",
        "software developer typing code",
        "hacker terminal screen",
        "developer working night",
    ],
    "audit_emerald":     [
        "cybersecurity analyst monitor",
        "security operations center",
        "data protection technology",
        "network security dashboard",
    ],
}

# Orientation and minimum resolution preferences
_MIN_WIDTH = 1280
_MIN_HEIGHT = 720


def _load_pexels_key() -> str | None:
    """Load PEXELS_API_KEY from environment or .env file."""
    # 1. Check environment variable directly
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if key:
        return key

    # 2. Parse .env file
    env_file = Path(r"d:\Animus-Studio\.env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("PEXELS_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val

    return None


def _search_pexels_video(query: str, api_key: str, per_page: int = 5) -> list[dict]:
    """Search Pexels Videos API. Returns list of video objects."""
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={per_page}&orientation=landscape"
    req = urllib.request.Request(url, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("videos", [])
    except Exception as exc:
        logger.warning("pexels.search_failed", query=query, error=str(exc))
        return []


def _pick_best_file(video: dict) -> str | None:
    """Pick the highest-resolution HD file link from a Pexels video object."""
    files = video.get("video_files", [])
    # Sort by width desc, prefer mp4
    files = sorted(
        [f for f in files if f.get("file_type", "") == "video/mp4"],
        key=lambda f: f.get("width", 0),
        reverse=True,
    )
    for f in files:
        if f.get("width", 0) >= _MIN_WIDTH and f.get("height", 0) >= _MIN_HEIGHT:
            return f.get("link")
    # Accept any mp4 if no HD found
    return files[0].get("link") if files else None


def _download_clip(url: str, dest: str) -> bool:
    """Download a video file from url to dest. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AnimusStudio/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
            while chunk := resp.read(65536):
                f.write(chunk)
        size = os.path.getsize(dest)
        return size > 50_000   # At least 50KB = real video
    except Exception as exc:
        logger.warning("pexels.download_failed", url=url, error=str(exc))
        return False


def _trim_clip_to_duration(src: str, dest: str, duration: float) -> str:
    """Trim/loop a video clip to exactly `duration` seconds using ffmpeg."""
    # Use -stream_loop -1 to loop if shorter than needed, then trim
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",   # Loop input if too short
        "-i", src,
        "-t", str(duration),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
        "-an",                  # Strip audio (we use our own TTS)
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "20",
        dest,
    ]
    result = subprocess.run(cmd, capture_output=True)
    return dest if os.path.exists(dest) and os.path.getsize(dest) > 1000 else src


import urllib.parse  # noqa: E402 (used above)


def download_stock_clip(
    section_type: str,
    duration: float,
    output_path: str,
    api_key: str,
) -> str | None:
    """
    Search Pexels for a relevant video clip, download and trim it.
    Returns the output_path on success, None on failure.
    """
    queries = _SECTION_QUERIES.get(section_type, ["technology server room"])
    raw_path = output_path.replace(".mp4", "_raw.mp4")

    for query in queries:
        logger.info("pexels.searching", query=query)
        videos = _search_pexels_video(query, api_key)
        for video in videos:
            link = _pick_best_file(video)
            if not link:
                continue
            logger.info("pexels.downloading", link=link[:60])
            if _download_clip(link, raw_path):
                trimmed = _trim_clip_to_duration(raw_path, output_path, duration)
                if os.path.exists(trimmed) and os.path.getsize(trimmed) > 1000:
                    logger.info("pexels.success", output=output_path)
                    # Clean up raw
                    try:
                        os.remove(raw_path)
                    except Exception:
                        pass
                    return output_path

    logger.warning("pexels.all_queries_failed", section_type=section_type)
    return None


def get_stock_bg_clip(
    section_type: str,
    duration: float,
    output_path: str,
) -> tuple[str, str]:
    """
    Primary entry point. Tries Pexels first, falls back to procedural animation.

    Returns:
        (path_to_mp4, source) where source is "pexels" or "procedural"
    """
    from agents.editor.motion_bg import pre_render_bg_mp4, STYLE_TO_BG

    api_key = _load_pexels_key()

    if api_key:
        logger.info("stock_footage.pexels_key_found", section_type=section_type)
        result = download_stock_clip(section_type, duration, output_path, api_key)
        if result:
            return result, "pexels"
        logger.warning("stock_footage.pexels_failed_falling_back")
    else:
        logger.info("stock_footage.no_pexels_key_using_procedural")

    # Fallback: procedural motion background
    bg_type = STYLE_TO_BG.get(section_type, "terminal_crash")
    proc_path = output_path.replace(".mp4", "_proc.mp4")
    pre_render_bg_mp4(bg_type, duration, proc_path)
    return proc_path, "procedural"
