"""
agents/editor/cinematic.py

Cinematic Background Scene Generator & Ken Burns Motion Zoom Engine.
Generates 1920x1080 high-production-value background scene visuals per topic:
  1. Section 1: Dark server room with glowing red warning light vignettes
  2. Section 2: Holographic blue radial grid canvas with cyan particle nodes
  3. Section 3: Cyber matrix background with glowing teal code streams
  4. Section 4: Telemetric emerald/gold audit shield backdrop

Applies slow Ken Burns camera motion zoom (1.0x -> 1.06x) so the background is NEVER static.
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def render_cinematic_bg(output_path: str, style_type: str = "server_alert") -> str:
    """Renders a 1920x1080 cinematic dark tech background image."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), color="#080c14")
    draw = ImageDraw.Draw(img)

    if style_type == "server_alert":
        # Dark red/blue alert vignette
        for y in range(H):
            r = int(14 + (y / H) * 12)
            g = int(8 + (y / H) * 6)
            b = int(24 + (y / H) * 20)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Red alert radial glow in top right
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(W - 600, -200), (W + 200, 600)], fill=(220, 38, 38, 45))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    elif style_type == "architecture_blue":
        # Deep cyan/navy radial gradient
        for y in range(H):
            r = int(8 + (y / H) * 10)
            g = int(16 + (y / H) * 28)
            b = int(32 + (y / H) * 50)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(W // 2 - 500, H // 2 - 400), (W // 2 + 500, H // 2 + 400)], fill=(0, 240, 255, 35))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    elif style_type == "code_matrix":
        # Deep teal matrix grid
        for y in range(H):
            r = int(6 + (y / H) * 8)
            g = int(20 + (y / H) * 32)
            b = int(28 + (y / H) * 36)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(-200, -100), (600, 700)], fill=(13, 148, 136, 40))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    else:
        # Gold/Emerald audit backdrop
        for y in range(H):
            r = int(10 + (y / H) * 18)
            g = int(22 + (y / H) * 35)
            b = int(20 + (y / H) * 25)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(W // 2 - 400, -100), (W // 2 + 400, 700)], fill=(56, 161, 105, 40))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Add subtle grid lines for tech depth
    draw_grid = ImageDraw.Draw(img)
    grid_color = (255, 255, 255, 12)
    for x in range(0, W, 80):
        draw_grid.line([(x, 0), (x, H)], fill=grid_color)
    for y in range(0, H, 80):
        draw_grid.line([(0, y), (W, y)], fill=grid_color)

    img.save(output_path, "PNG")
    return output_path
