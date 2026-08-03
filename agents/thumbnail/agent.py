"""
agents/thumbnail/agent.py

Thumbnail Agent — Department: Creative

Renders high-CTR 1280x720 branded YouTube thumbnail images:
  1. Dark mode gradient canvas (#0b0f19 to #161f36)
  2. Neon cyan accent border (#00f0ff)
  3. Bold high-contrast typography
  4. AnimusLab brand badge & subtitle tags
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont

import structlog
from agents.base import BaseAgent, AgentContext

logger = structlog.get_logger()
OUTPUT_DIR = Path("outputs")


def _resolve_font_file(bold: bool = True) -> str | None:
    win_fonts = r"C:\Windows\Fonts"
    if os.path.exists(win_fonts):
        f = os.path.join(win_fonts, "arialbd.ttf" if bold else "arial.ttf")
        if os.path.exists(f):
            return f
    return None


class ThumbnailAgent(BaseAgent):
    name = "thumbnail"
    department = "creative"
    produces = {"thumbnail_path"}

    async def _run(self, rt_or_ctx: Any, spec_or_input: Any, exec_or_none: Any = None) -> dict[str, Any]:
        if exec_or_none is not None:
            exec_ctx = exec_or_none
            script = exec_ctx.get("script", {})
            brand_info = exec_ctx.get("brand", {})
            job_id = exec_ctx.execution_id
        else:
            context = rt_or_ctx
            input_data = spec_or_input or {}
            script = context.get("script", input_data.get("script", {}))
            brand_info = getattr(context, "brand", {}) or input_data.get("brand", {})
            job_id = getattr(context, "job_id", f"job_{int(os.times().system * 100)}")

        title = script.get("title") or input_data.get("title") or "Deterministic AI Systems"
        brand_name = brand_info.get("name", "ANIMUSLAB ENGINEERING").upper()

        self._log.info("thumbnail.rendering", title=title, job_id=job_id)

        out_dir = OUTPUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_path = str((out_dir / "thumbnail.png").resolve())

        # Render 1280x720 canvas
        width, height = 1280, 720
        img = Image.new("RGB", (width, height), color="#0b0f19")
        draw = ImageDraw.Draw(img)

        # Draw dark gradient lines
        for y in range(height):
            ratio = y / height
            r = int(11 * (1 - ratio) + 22 * ratio)
            g = int(15 * (1 - ratio) + 31 * ratio)
            b = int(25 * (1 - ratio) + 54 * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Draw neon cyan accent frame border (8px)
        accent_color = "#00f0ff"
        draw.rectangle([(0, 0), (width - 1, height - 1)], outline=accent_color, width=8)

        # Load fonts
        font_path_bold = _resolve_font_file(bold=True)
        font_path_reg = _resolve_font_file(bold=False)

        try:
            font_title = ImageFont.truetype(font_path_bold, 54) if font_path_bold else ImageFont.load_default()
            font_badge = ImageFont.truetype(font_path_bold, 24) if font_path_bold else ImageFont.load_default()
            font_tag = ImageFont.truetype(font_path_reg, 22) if font_path_reg else ImageFont.load_default()
        except Exception:
            font_title = ImageFont.load_default()
            font_badge = ImageFont.load_default()
            font_tag = ImageFont.load_default()

        # 1. Top Left Brand Badge Box
        draw.rectangle([(60, 50), (450, 95)], fill="#161f36", outline=accent_color, width=2)
        draw.text((80, 60), f"// {brand_name}", fill=accent_color, font=font_badge)

        # 2. Centered High-CTR Title Text
        wrapped_lines = textwrap.wrap(title.upper(), width=24)
        start_y = 220
        for i, line in enumerate(wrapped_lines[:3]):
            fill_color = "white" if i % 2 == 0 else accent_color
            draw.text((60, start_y + (i * 70)), line, fill=fill_color, font=font_title)

        # 3. Bottom Tag Badge
        draw.rectangle([(60, 600), (360, 650)], fill="#00f0ff")
        draw.text((80, 612), "ARCHITECTURE V2", fill="#0b0f19", font=font_badge)

        # Save output PNG
        img.save(thumbnail_path, format="PNG")
        self._log.info("thumbnail.done", output=thumbnail_path)

        if hasattr(rt_or_ctx, "set"):
            rt_or_ctx.set("thumbnail_path", thumbnail_path)

        return {"thumbnail_path": thumbnail_path}
