"""
agents/editor/visuals.py

Cinematic Tech Visual Engine & Pillow-Padded Text Renderer for EditorAgent.
Renders high-end 1080p visual assets:
  1. Zero-clipping Pillow text overlays (Headers, Watermark, Intro Badges)
  2. Glassmorphic Cards with Neon Cyan/Purple Gradients & Rounded Corners
  3. Dynamic Terminal Window, Architecture Diagrams, Code Blocks & Telemetry Cards
  4. Fixes all typos (e.g. 'Reliability')
"""
from __future__ import annotations

import os
import textwrap
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
    """Renders a text string into a transparent PNG with safe top/bottom padding to prevent font clipping."""
    font = _resolve_font(size=font_size, bold=bold)

    # Temporary canvas to measure exact text bounding box
    dummy = Image.new("RGBA", (100, 100))
    dummy_draw = ImageDraw.Draw(dummy)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)

    text_w = bbox[2] - bbox[0] + 40
    text_h = bbox[3] - bbox[1] + 40

    img = Image.new("RGBA", (max(text_w, 200), max(text_h, 60)), bg_color)
    draw = ImageDraw.Draw(img)

    # Render text with 20px top padding (prevents top ascender clipping)
    draw.text((20, 20 - bbox[1]), text, fill=color, font=font)
    img.save(output_path, "PNG")
    return output_path


def render_terminal_card(output_path: str, section_title: str = "Production System") -> str:
    """Renders a glassmorphic terminal window showing silent production failure logs."""
    W, H = 1240, 620
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark Glass Card Canvas (#0d1322 with rounded corners)
    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)

    # 2. Window Header Bar
    draw.rounded_rectangle([(0, 0), (W, 50)], radius=20, fill="#161f36")
    draw.rectangle([(0, 30), (W, 50)], fill="#161f36")  # Fill bottom rounded corners of header

    # Red, Yellow, Green Window Controls
    draw.ellipse([(24, 17), (38, 31)], fill="#ff5f56")
    draw.ellipse([(48, 17), (62, 31)], fill="#ffbd2e")
    draw.ellipse([(72, 17), (86, 31)], fill="#27c93f")

    font_term = _resolve_font(20, bold=False)
    draw.text((110, 14), f"bash - animus@production: {section_title.lower()}", fill="#a0aec0", font=font_term)

    # 3. Terminal Log Lines
    lines = [
        ("animus@kernel:~$ ", "#00f0ff", "deploy --environment=production --target=llm_agent"),
        ("[INFO 10:42:01] ", "#27c93f", "Agent container started with ID: container_88f921"),
        ("[INFO 10:42:15] ", "#27c93f", "Prompt evaluation passed (staging verification score: 0.98)"),
        ("[WARN 11:02:44] ", "#ffbd2e", "SILENT STATE DRIFT DETECTED: Model output context variance > 45%"),
        ("[ERROR 11:02:45] ", "#ff5f56", "NON-DETERMINISTIC BEHAVIOR: LLM changed decision without code mutation"),
        ("[CRIT 11:02:45] ", "#ff5f56", "FAIL: System boundary missing kernel execution wrapper!"),
        ("animus@kernel:~$ ", "#00f0ff", "governance doctor --inspect-failure"),
    ]

    start_y = 80
    for prefix, color, text in lines:
        draw.text((35, start_y), prefix, fill=color, font=font_term)
        prefix_width = len(prefix) * 12
        draw.text((35 + prefix_width, start_y), text, fill="#e2e8f0", font=font_term)
        start_y += 70

    img.save(output_path, "PNG")
    return output_path


def render_architecture_card(output_path: str, section_title: str = "") -> str:
    """Renders a glowing 4-node system architecture diagram with 100% padded text boxes."""
    W, H = 1240, 620
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_header = _resolve_font(22, bold=True)
    font_title = _resolve_font(18, bold=True)
    font_sub = _resolve_font(15, bold=False)

    # Outer Glass Canvas
    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)
    draw.text((40, 25), "// ANIMUSLAB SYSTEM ARCHITECTURE PROTOCOL", fill="#00f0ff", font=font_header)

    # 4 Node Boxes (250px wide each, 295px step)
    nodes = [
        (35, 210, "USER PROMPT", "Raw Input Intent", "#3182ce"),
        (330, 210, "RUNTIME KERNEL", "Deterministic State", "#00f0ff"),
        (625, 210, "LLM ENGINE", "Nondeterministic Model", "#e53e3e"),
        (920, 210, "PROVENANCE LOG", "Audit Record", "#38a169"),
    ]

    for x, y, label, sub, color in nodes:
        draw.rounded_rectangle([(x, y), (x + 250, y + 170)], radius=14, fill="#161f36", outline=color, width=3)
        draw.text((x + 18, y + 38), label, fill=color, font=font_title)
        draw.text((x + 18, y + 95), sub, fill="#a0aec0", font=font_sub)

    # Connecting Arrows
    arrows = [
        (285, 295, 330, 295),
        (580, 295, 625, 295),
        (875, 295, 920, 295),
    ]
    for x1, y1, x2, y2 in arrows:
        draw.line([(x1, y1), (x2, y2)], fill="#00f0ff", width=4)
        draw.polygon([(x2 - 12, y2 - 8), (x2, y2), (x2 - 12, y2 + 8)], fill="#00f0ff")

    img.save(output_path, "PNG")
    return output_path


def render_code_card(output_path: str, section_title: str = "") -> str:
    """Renders a syntax-highlighted code block card."""
    W, H = 1240, 620
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
        ("    # 1. State lock context", "#718096"),
        ("    context = await runtime.acquire_state_lock(mission_spec)", "#e2e8f0"),
        ("    # 2. Execute LLM decision with audit capture", "#718096"),
        ("    result = await llm.chat_with_provenance(context)", "#e2e8f0"),
        ("    # 3. Cryptographically sign execution record", "#718096"),
        ("    return await MissionRecord.commit(result)", "#38a169"),
    ]

    start_y = 80
    for text, color in code_lines:
        draw.text((45, start_y), text, fill=color, font=font)
        start_y += 62

    img.save(output_path, "PNG")
    return output_path


def render_metric_card(output_path: str, section_title: str = "") -> str:
    """Renders a telemetric callout metric card with tight vertical spacing."""
    W, H = 1240, 620
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_percent = _resolve_font(76, bold=True)
    font_title = _resolve_font(24, bold=True)
    font_sub = _resolve_font(18, bold=False)

    draw.rounded_rectangle([(0, 0), (W, H)], radius=20, fill="#0d1322", outline="#00f0ff", width=3)

    # Box 1
    draw.rounded_rectangle([(80, 100), (560, 520)], radius=16, fill="#161f36", outline="#00f0ff", width=3)
    draw.text((120, 150), "0%", fill="#ffea00", font=font_percent)
    draw.text((120, 260), "SILENT STATE DRIFT", fill="#ffffff", font=font_title)
    draw.text((120, 320), "Deterministic Runtime Guarantee", fill="#a0aec0", font=font_sub)

    # Box 2
    draw.rounded_rectangle([(680, 100), (1160, 520)], radius=16, fill="#161f36", outline="#38a169", width=3)
    draw.text((720, 150), "100%", fill="#38a169", font=font_percent)
    draw.text((720, 260), "AUDIT TRACEABILITY", fill="#ffffff", font=font_title)
    draw.text((720, 320), "Cryptographic MissionRecord", fill="#a0aec0", font=font_sub)

    img.save(output_path, "PNG")
    return output_path
