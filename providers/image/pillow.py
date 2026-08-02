"""
Pillow Image Provider — template-based thumbnail generation

No AI, no external API. Produces branded thumbnails using:
  - Brand gradient background
  - Bold title text
  - Logo watermark
  - Accent strip

Always available (Pillow is a base dependency).
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from runtime.capabilities import Capability


class PillowProvider:
    name = "pillow"
    priority = 10
    is_cloud = False
    capabilities = {Capability.IMAGE_GENERATION}
    model = "pillow/template"


    def is_available(self) -> bool:
        try:
            from PIL import Image  # noqa: F401
            return True
        except ImportError:
            return False

    async def generate_thumbnail(
        self,
        title: str,
        output_path: str,
        brand: dict[str, Any] | None = None,
        size: tuple[int, int] = (1280, 720),
    ) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._render_blocking, title, output_path, brand or {}, size
        )

    def _render_blocking(
        self,
        title: str,
        output_path: str,
        brand: dict[str, Any],
        size: tuple[int, int],
    ) -> str:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        W, H = size
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # ── Background gradient ───────────────────────────────
        c1 = _hex_rgb(brand.get("primary_color", "#0f0f23"))
        c2 = _hex_rgb(brand.get("secondary_color", "#1a1a3e"))
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        for x in range(W):
            t = x / W
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            draw.line([(x, 0), (x, H)], fill=(r, g, b))

        # ── Accent strip ─────────────────────────────────────
        accent = _hex_rgb(brand.get("accent_color", "#6c63ff"))
        draw.rectangle([0, H - 12, W, H], fill=accent)

        # ── Title text ───────────────────────────────────────
        text_color = brand.get("text_color", "#ffffff")
        font_size  = 72 if len(title) < 40 else 54
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
            small_font = ImageFont.truetype("arial.ttf", 32)
        except IOError:
            font = ImageFont.load_default()
            small_font = font

        wrapped = textwrap.fill(title, width=28)
        # Shadow
        draw.multiline_text((84, 194), wrapped, font=font, fill=(0, 0, 0, 128), spacing=12)
        draw.multiline_text((80, 190), wrapped, font=font, fill=text_color, spacing=12)

        # ── Brand name watermark ─────────────────────────────
        name = brand.get("name", "Animus")
        draw.text((80, H - 80), name, font=small_font, fill=(*accent, 200))

        img.save(output_path, "JPEG", quality=95)
        return output_path


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (15, 15, 35)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
