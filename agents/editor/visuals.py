"""
agents/editor/visuals.py

Cinematic Visual Card Engine for EditorAgent.
Renders 8 distinct high-production-value visual cards:
  1. Terminal Card (Bash execution log)
  2. Architecture Card (4-node protocol flow diagram)
  3. Code Card (Python kernel governance lock snippet)
  4. Metric Card (0% drift / 100% audit telemetry)
  5. Callout Card (High-impact quote banner)
  6. Comparison Card (Nondeterministic LLM vs Governed Kernel)
  7. Pipeline Card (5-stage mission pipeline flow)
  8. Provenance Card (Cryptographic audit hash signature)
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _resolve_font(size: int = 24, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    win_fonts = r"C:\Windows\Fonts"
    font_name = "arialbd.ttf" if bold else "arial.ttf"
    font_path = os.path.join(win_fonts, font_name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_padded_text_png(
    output_path: str,
    text: str,
    font_size: int = 28,
    color: str = "#00f0ff",
    bold: bool = True,
    bg_color: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> str:
    """Renders text into a transparent PNG with safe padding to prevent font clipping."""
    font = _resolve_font(size=font_size, bold=bold)

    dummy = Image.new("RGBA", (100, 100))
    dummy_draw = ImageDraw.Draw(dummy)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)

    text_w = bbox[2] - bbox[0] + 40
    text_h = bbox[3] - bbox[1] + 40

    img = Image.new("RGBA", (max(text_w, 200), max(text_h, 60)), bg_color)
    draw = ImageDraw.Draw(img)

    draw.text((20, 20 - bbox[1]), text, fill=color, font=font)
    img.save(output_path, "PNG")
    return output_path


def render_terminal_card(output_path: str, section_title: str = "Production System") -> str:
    """Renders a glassmorphic terminal window with production failure logs."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)
    draw.rounded_rectangle([(0, 0), (W, 50)], radius=20, fill="#161f36")
    draw.rectangle([(0, 30), (W, 50)], fill="#161f36")

    draw.ellipse([(24, 17), (38, 31)], fill="#ff5f56")
    draw.ellipse([(48, 17), (62, 31)], fill="#ffbd2e")
    draw.ellipse([(72, 17), (86, 31)], fill="#27c93f")

    font_term = _resolve_font(20, bold=False)
    draw.text((110, 14), f"bash - animus@production: {section_title.lower()}", fill="#a0aec0", font=font_term)

    lines = [
        ("animus@kernel:~$ ", "#00f0ff", "deploy --environment=production --target=llm_agent"),
        ("[INFO 10:42:01] ", "#27c93f", "Agent container started with ID: container_88f921"),
        ("[INFO 10:42:15] ", "#27c93f", "Prompt evaluation passed (staging score: 0.98)"),
        ("[WARN 11:02:44] ", "#ffbd2e", "SILENT STATE DRIFT DETECTED: Context variance > 45%"),
        ("[ERROR 11:02:45] ", "#ff5f56", "NON-DETERMINISTIC BEHAVIOR: LLM output mutated"),
        ("[CRIT 11:02:45] ", "#ff5f56", "FAIL: System boundary missing kernel wrapper!"),
        ("animus@kernel:~$ ", "#00f0ff", "governance doctor --inspect-failure"),
    ]

    start_y = 75
    for prefix, color, text in lines:
        draw.text((35, start_y), prefix, fill=color, font=font_term)
        prefix_width = len(prefix) * 12
        draw.text((35 + prefix_width, start_y), text, fill="#e2e8f0", font=font_term)
        start_y += 65

    img.save(output_path, "PNG")
    return output_path


def render_architecture_card(output_path: str) -> str:
    """Renders a glowing 4-node system architecture diagram."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_header = _resolve_font(22, bold=True)
    font_title = _resolve_font(18, bold=True)
    font_sub = _resolve_font(15, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)
    draw.text((40, 25), "// ANIMUSLAB SYSTEM ARCHITECTURE PROTOCOL", fill="#00f0ff", font=font_header)

    nodes = [
        (35, 180, "USER PROMPT", "Raw Input Intent", "#3182ce"),
        (330, 180, "RUNTIME KERNEL", "Deterministic State", "#00f0ff"),
        (625, 180, "LLM ENGINE", "Nondeterministic Model", "#e53e3e"),
        (920, 180, "PROVENANCE LOG", "Audit Record", "#38a169"),
    ]

    for x, y, label, sub, color in nodes:
        draw.rounded_rectangle([(x, y), (x + 250, y + 170)], radius=14, fill="#161f36", outline=color, width=3)
        draw.text((x + 18, y + 38), label, fill=color, font=font_title)
        draw.text((x + 18, y + 95), sub, fill="#a0aec0", font=font_sub)

    arrows = [
        (285, 265, 330, 265),
        (580, 265, 625, 265),
        (875, 265, 920, 265),
    ]
    for x1, y1, x2, y2 in arrows:
        draw.line([(x1, y1), (x2, y2)], fill="#00f0ff", width=4)
        draw.polygon([(x2 - 12, y2 - 8), (x2, y2), (x2 - 12, y2 + 8)], fill="#00f0ff")

    img.save(output_path, "PNG")
    return output_path


def render_code_card(output_path: str) -> str:
    """Renders a syntax-highlighted code block card."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = _resolve_font(20, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)
    draw.rounded_rectangle([(0, 0), (W, 50)], radius=20, fill="#161f36")
    draw.rectangle([(0, 30), (W, 50)], fill="#161f36")
    draw.text((35, 14), "python - runtime/kernel.py", fill="#00f0ff", font=font)

    code_lines = [
        ("@kernel.governed(name='production_pipeline')", "#d69e2e"),
        ("async def run_governed_agent(mission_spec: MissionSpec):", "#4299e1"),
        ("    # 1. Acquire deterministic state lock", "#718096"),
        ("    context = await runtime.acquire_state_lock(mission_spec)", "#e2e8f0"),
        ("    # 2. Execute LLM decision with audit capture", "#718096"),
        ("    result = await llm.chat_with_provenance(context)", "#e2e8f0"),
        ("    # 3. Cryptographically sign execution record", "#718096"),
        ("    return await MissionRecord.commit(result)", "#38a169"),
    ]

    start_y = 75
    for text, color in code_lines:
        draw.text((45, start_y), text, fill=color, font=font)
        start_y += 58

    img.save(output_path, "PNG")
    return output_path


def render_metric_card(output_path: str) -> str:
    """Renders telemetric callout metric cards."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_percent = _resolve_font(72, bold=True)
    font_title = _resolve_font(24, bold=True)
    font_sub = _resolve_font(18, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)

    draw.rounded_rectangle([(80, 80), (560, 480)], radius=16, fill="#161f36", outline="#00f0ff", width=3)
    draw.text((120, 130), "0%", fill="#ffea00", font=font_percent)
    draw.text((120, 240), "SILENT STATE DRIFT", fill="#ffffff", font=font_title)
    draw.text((120, 300), "Deterministic Runtime Guarantee", fill="#a0aec0", font=font_sub)

    draw.rounded_rectangle([(680, 80), (1160, 480)], radius=16, fill="#161f36", outline="#38a169", width=3)
    draw.text((720, 130), "100%", fill="#38a169", font=font_percent)
    draw.text((720, 240), "AUDIT TRACEABILITY", fill="#ffffff", font=font_title)
    draw.text((720, 300), "Cryptographic MissionRecord", fill="#a0aec0", font=font_sub)

    img.save(output_path, "PNG")
    return output_path


def render_callout_card(output_path: str) -> str:
    """Renders a high-impact engineering quote callout card."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_quote = _resolve_font(32, bold=True)
    font_sub = _resolve_font(20, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#7928ca", width=3)
    draw.text((60, 60), "// ENGINEERING PRINCIPLE", fill="#7928ca", font=_resolve_font(22, bold=True))

    quote = '"Prompts provide user intent,\nbut only Deterministic Governance\nguarantees production reliability."'
    draw.text((60, 150), quote, fill="#ffffff", font=font_quote)

    draw.text((60, 440), "— Animus Studio Architecture Manifesto", fill="#a0aec0", font=font_sub)

    img.save(output_path, "PNG")
    return output_path


def render_comparison_card(output_path: str) -> str:
    """Renders a side-by-side comparison: Ungoverned LLM vs Governed Animus Kernel."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_title = _resolve_font(22, bold=True)
    font_body = _resolve_font(18, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)

    # Left Column: Raw LLM (Red Border)
    draw.rounded_rectangle([(60, 60), (580, 500)], radius=16, fill="#161f36", outline="#e53e3e", width=3)
    draw.text((90, 90), "❌ RAW PROMPT AGENTS", fill="#e53e3e", font=font_title)
    raw_points = [
        "• Silent state drift in production",
        "• Non-deterministic execution paths",
        "• Zero audit provenance log",
        "• Breaks silently on model updates",
    ]
    y_p = 160
    for pt in raw_points:
        draw.text((90, y_p), pt, fill="#e2e8f0", font=font_body)
        y_p += 70

    # Right Column: Animus Kernel (Cyan Border)
    draw.rounded_rectangle([(660, 60), (1180, 500)], radius=16, fill="#161f36", outline="#00f0ff", width=3)
    draw.text((690, 90), "⚡ ANIMUS DETERMINISTIC KERNEL", fill="#00f0ff", font=font_title)
    gov_points = [
        "• State lock contract enforcement",
        "• Guaranteed reproducible execution",
        "• Signed cryptographic MissionRecord",
        "• Automatic Health Doctor repair",
    ]
    y_p = 160
    for pt in gov_points:
        draw.text((690, y_p), pt, fill="#e2e8f0", font=font_body)
        y_p += 70

    img.save(output_path, "PNG")
    return output_path


def render_pipeline_card(output_path: str) -> str:
    """Renders a 5-stage mission execution pipeline flow."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_title = _resolve_font(20, bold=True)
    font_sub = _resolve_font(14, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)
    draw.text((40, 30), "// ANIMUS END-TO-END ORGANISM PIPELINE", fill="#00f0ff", font=_resolve_font(22, bold=True))

    stages = [
        ("01", "RESEARCH", "#3182ce"),
        ("02", "OUTLINE", "#805ad5"),
        ("03", "SCRIPT", "#dd6b20"),
        ("04", "VOICE", "#319795"),
        ("05", "EDITOR", "#38a169"),
    ]

    for idx, (num, name, color) in enumerate(stages):
        x = 40 + idx * 230
        y = 180
        draw.rounded_rectangle([(x, y), (x + 200, y + 220)], radius=14, fill="#161f36", outline=color, width=3)
        draw.text((x + 20, y + 25), num, fill=color, font=_resolve_font(36, bold=True))
        draw.text((x + 20, y + 100), name, fill="#ffffff", font=font_title)
        draw.text((x + 20, y + 155), "Verified Stage", fill="#a0aec0", font=font_sub)

    img.save(output_path, "PNG")
    return output_path


def render_provenance_card(output_path: str) -> str:
    """Renders a cryptographic MissionRecord audit provenance card."""
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_code = _resolve_font(19, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#38a169", width=3)
    draw.rounded_rectangle([(0, 0), (W, 50)], radius=20, fill="#161f36")
    draw.rectangle([(0, 30), (W, 50)], fill="#161f36")
    draw.text((35, 14), "json - storage/mission_records/alpha1_flagship.json", fill="#38a169", font=font_code)

    json_lines = [
        ('{', '#e2e8f0'),
        ('  "mission_id": "alpha1_flagship",', '#00f0ff'),
        ('  "status": "COMPLETED",', '#38a169'),
        ('  "governance": { "deterministic_lock": true, "state_drift": 0.0 },', '#d69e2e'),
        ('  "provenance_hash": "sha256:8f92a1c07e4d8b2e3f5a...",', '#4299e1'),
        ('  "replay_engine_ready": true', '#38a169'),
        ('}', '#e2e8f0'),
    ]

    start_y = 80
    for text, color in json_lines:
        draw.text((45, start_y), text, fill=color, font=font_code)
        start_y += 62

    img.save(output_path, "PNG")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  CINEMATIC HUD OVERLAYS — Broadcast lower-thirds and corner badges
#  These replace the full-screen opaque cards.
#  Coverage: lower-third ≤18% of frame height, corner badges ≤8%.
# ═══════════════════════════════════════════════════════════════════════════

def render_lower_third(
    output_path: str,
    title: str,
    subtitle: str = "",
    accent_color: str = "#00f0ff",
    w: int = 1920,
    h: int = 1080,
) -> str:
    """
    Renders a broadcast-style lower-third HUD strip as a transparent RGBA PNG.
    Height: ~18% of frame (190px). Semi-transparent dark gradient bottom strip.
    Left accent bar + large title + small subtitle. Background is FULLY visible above.
    """
    strip_h = 185
    fade_h  = 60
    accent_w = 6
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradient fade zone above strip (transparent -> semi-opaque)
    for dy in range(fade_h):
        alpha = int(145 * (dy / fade_h))
        draw.rectangle(
            [(0, h - strip_h - fade_h + dy), (w, h - strip_h - fade_h + dy + 1)],
            fill=(0, 0, 0, alpha),
        )

    # Solid semi-transparent strip
    draw.rectangle([(0, h - strip_h), (w, h)], fill=(0, 0, 0, 172))

    # Left accent bar
    r_a = int(accent_color[1:3], 16)
    g_a = int(accent_color[3:5], 16)
    b_a = int(accent_color[5:7], 16)
    draw.rectangle([(0, h - strip_h), (accent_w, h)], fill=(r_a, g_a, b_a, 255))

    # Title text
    try:
        f_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 42)
    except Exception:
        f_title = ImageFont.load_default()
    draw.text((accent_w + 30, h - strip_h + 26), title, fill=(255, 255, 255, 240), font=f_title)

    # Subtitle
    if subtitle:
        try:
            f_sub = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 26)
        except Exception:
            f_sub = ImageFont.load_default()
        draw.text(
            (accent_w + 32, h - strip_h + 82),
            subtitle,
            fill=(r_a, g_a, b_a, 200),
            font=f_sub,
        )

    img.save(output_path, "PNG")
    return output_path


def render_corner_metric(
    output_path: str,
    value: str,
    label: str,
    accent_color: str = "#ffcc00",
    corner: str = "tr",
    w: int = 1920,
    h: int = 1080,
) -> str:
    """Renders a small glassy corner metric badge as a transparent RGBA PNG."""
    badge_w, badge_h = 260, 100
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad_x = 24
    bx = pad_x if corner.endswith("l") else w - badge_w - pad_x
    if corner.startswith("t"):
        by = 60 + pad_x  # Below top 60px letterbox bar
    else:
        by = h - 60 - pad_x - badge_h  # Above bottom 60px letterbox bar

    r_a = int(accent_color[1:3], 16)
    g_a = int(accent_color[3:5], 16)
    b_a = int(accent_color[5:7], 16)

    draw.rounded_rectangle(
        [(bx, by), (bx + badge_w, by + badge_h)],
        radius=12,
        fill=(0, 0, 0, 150),
        outline=(r_a, g_a, b_a, 200),
        width=2,
    )

    try:
        f_val = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
        f_lbl = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 17)
    except Exception:
        f_val = f_lbl = ImageFont.load_default()

    draw.text((bx + 18, by + 10), value, fill=accent_color, font=f_val)
    draw.text((bx + 18, by + 58), label, fill=(200, 200, 200, 220), font=f_lbl)

    img.save(output_path, "PNG")
    return output_path
