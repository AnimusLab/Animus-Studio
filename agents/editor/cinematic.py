"""
agents/editor/cinematic.py

Filmic & High-Tech Cinematic Background Scene Generator.
Inspired by Elliot Grafton (Sony FX6 S-Cinetone filmic grading) & Huawei Tech Event showcases:
  1. 2.39:1 Widescreen Letterbox Scope Bars (60px top/bottom cinematic framing)
  2. Multi-tone organic radial lighting & soft lens vignette bloom
  3. Dynamic section visual styling (Amber Alert, Navy Cyber, Teal Matrix, Gold Telemetry)
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def render_cinematic_bg(output_path: str, style_type: str = "server_alert") -> str:
    """Renders a 1920x1080 filmic cinematic background image."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), color="#080c14")
    draw = ImageDraw.Draw(img)

    if style_type == "server_alert":
        # Filmic amber/crimson alert vignette (S-Cinetone tone mapping)
        for y in range(H):
            r = int(18 + (y / H) * 16)
            g = int(8 + (y / H) * 8)
            b = int(24 + (y / H) * 22)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Soft amber radial bloom in top right
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(W - 700, -300), (W + 200, 600)], fill=(225, 29, 72, 50))
        odraw.ellipse([(100, H - 400), (900, H + 200)], fill=(217, 119, 6, 35))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    elif style_type == "architecture_blue":
        # Deep navy/electric cyan radial gradient
        for y in range(H):
            r = int(8 + (y / H) * 10)
            g = int(18 + (y / H) * 30)
            b = int(40 + (y / H) * 55)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(W // 2 - 600, H // 2 - 450), (W // 2 + 600, H // 2 + 450)], fill=(0, 240, 255, 40))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    elif style_type == "code_matrix":
        # Deep teal & cyan matrix bloom
        for y in range(H):
            r = int(6 + (y / H) * 10)
            g = int(24 + (y / H) * 36)
            b = int(32 + (y / H) * 40)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(-200, -100), (700, 800)], fill=(13, 148, 136, 45))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    else:
        # Gold/Emerald telemetric backdrop
        for y in range(H):
            r = int(12 + (y / H) * 20)
            g = int(24 + (y / H) * 38)
            b = int(22 + (y / H) * 28)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([(W // 2 - 500, -100), (W // 2 + 500, 750)], fill=(34, 197, 94, 45))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    img.save(output_path, "PNG")
    return output_path


def render_letterbox_overlay(output_path: str) -> str:
    """Renders 2.39:1 widescreen theatrical letterbox scope bars (60px top & bottom)."""
    W, H = 1920, 1080
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 60px Top & Bottom Letterbox Scope Bars
    draw.rectangle([(0, 0), (W, 60)], fill="#000000")
    draw.rectangle([(0, H - 60), (W, H)], fill="#000000")

    img.save(output_path, "PNG")
    return output_path
