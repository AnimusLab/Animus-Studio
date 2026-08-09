"""
agents/editor/cinematic.py

Photorealistic AI Visual B-Roll & Cinematic Scene Generator Engine.
Uses 8K AI-generated cinematic visual backgrounds:
  1. Section 1: Cyberpunk server room with red alert lights (bg_server_crisis.png)
  2. Section 2: High-tech holographic neural network blueprint (bg_neural_blueprint.png)
  3. Section 3: Futuristic neon teal code matrix screen (bg_code_matrix.png)
  4. Section 4: Golden 3D holographic security shield core (bg_governance_shield.png)

Combines AI visual B-roll with 2.39:1 widescreen scope framing & dark vignette contrast layers.
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance

ASSETS_DIR = Path(r"d:\Animus-Studio\assets\cinematic")


def render_cinematic_bg(output_path: str, style_type: str = "server_alert") -> str:
    """Renders a 1920x1080 photorealistic AI visual background with vignette contrast."""
    W, H = 1920, 1080

    mapping = {
        "server_alert": ASSETS_DIR / "bg_server_crisis.png",
        "architecture_blue": ASSETS_DIR / "bg_neural_blueprint.png",
        "code_matrix": ASSETS_DIR / "bg_code_matrix.png",
        "audit_emerald": ASSETS_DIR / "bg_governance_shield.png",
    }

    asset_file = mapping.get(style_type, ASSETS_DIR / "bg_server_crisis.png")

    if asset_file.exists():
        img = Image.open(asset_file).convert("RGB")
        img = img.resize((W, H), Image.Resampling.LANCZOS)
        # Darken image slightly (0.7x) so glass visual cards pop with high contrast
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.65)
    else:
        img = Image.new("RGB", (W, H), color="#080c14")

    # Add dark vignette contrast around borders
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    # Dark radial vignette frame
    odraw.rectangle([(0, 0), (W, H)], fill=(0, 0, 0, 40))
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
