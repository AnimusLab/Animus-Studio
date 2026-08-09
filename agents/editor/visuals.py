"""
agents/editor/visuals.py

Dynamic Screen Activity & High-Context Visual Component Generator for EditorAgent.
Renders 1200x600 high-resolution visual cards using Pillow:
  1. Animated Terminal Window (Error logs, silent drift warnings, kernel execution)
  2. System Architecture Flowchart (Prompt -> Runtime Kernel -> LLM -> Provenance Log)
  3. Code Highlight Card (Python/Rust kernel decorator code snippets)
  4. Telemetry & Metric Card (0% State Drift, 100% Audit Traceability)
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _resolve_font(size: int = 22, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    win_fonts = r"C:\Windows\Fonts"
    font_name = "consola.ttf" if not bold else "consolab.ttf"
    font_path = os.path.join(win_fonts, font_name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_terminal_card(output_path: str, section_title: str = "Production System") -> str:
    """Renders an interactive dark terminal window showing silent production failure logs."""
    W, H = 1200, 600
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark Terminal Canvas (#0f1420)
    draw.rectangle([(0, 0), (W, H)], fill="#0f1420", outline="#00f0ff", width=2)

    # 2. Window Header Bar
    draw.rectangle([(0, 0), (W, 44)], fill="#1a2236")
    draw.ellipse([(20, 14), (32, 26)], fill="#ff5f56")
    draw.ellipse([(40, 14), (52, 26)], fill="#ffbd2e")
    draw.ellipse([(60, 14), (72, 26)], fill="#27c93f")

    font = _resolve_font(20, bold=False)
    draw.text((90, 12), f"bash - animus@production: {section_title.lower()}", fill="#a0aec0", font=font)

    # 3. Terminal Log Output Lines
    lines = [
        ("animus@kernel:~$ ", "#00f0ff", "deploy --environment=production --target=llm_agent"),
        ("[INFO 10:42:01] ", "#27c93f", "Agent container started with ID: container_88f921"),
        ("[INFO 10:42:15] ", "#27c93f", "Prompt evaluation passed (staging verification score: 0.98)"),
        ("[WARN 11:02:44] ", "#ffbd2e", "SILENT STATE DRIFT DETECTED: Model output context variance > 45%"),
        ("[ERROR 11:02:45] ", "#ff5f56", "NON-DETERMINISTIC BEHAVIOR: LLM changed decision without code mutation"),
        ("[CRIT 11:02:45] ", "#ff5f56", "FAIL: System boundary missing kernel execution wrapper!"),
        ("animus@kernel:~$ ", "#00f0ff", "governance doctor --inspect-failure"),
    ]

    start_y = 70
    for prefix, color, text in lines:
        draw.text((30, start_y), prefix, fill=color, font=font)
        prefix_width = len(prefix) * 12
        draw.text((30 + prefix_width, start_y), text, fill="#e2e8f0", font=font)
        start_y += 65

    img.save(output_path, "PNG")
    return output_path


def render_architecture_card(output_path: str, section_title: str = "") -> str:
    """Renders a glowing 4-node system architecture diagram with perfectly padded text boxes."""
    W, H = 1200, 600
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_header = _resolve_font(22, bold=True)
    font_title = _resolve_font(18, bold=True)
    font_sub = _resolve_font(15, bold=False)

    # Canvas Frame
    draw.rectangle([(0, 0), (W, H)], fill="#0f1420", outline="#00f0ff", width=2)
    draw.text((40, 25), "// ANIMUSLAB SYSTEM ARCHITECTURE PROTOCOL", fill="#00f0ff", font=font_header)

    # Node boxes: 240px wide each, 290px step
    nodes = [
        (35, 210, "USER PROMPT", "Raw Input Intent", "#3182ce"),
        (325, 210, "RUNTIME KERNEL", "Deterministic State", "#00f0ff"),
        (615, 210, "LLM ENGINE", "Nondeterministic Model", "#e53e3e"),
        (905, 210, "PROVENANCE LOG", "Audit Record", "#38a169"),
    ]

    for x, y, label, sub, color in nodes:
        draw.rectangle([(x, y), (x + 240, y + 170)], fill="#1a2236", outline=color, width=3)
        draw.text((x + 18, y + 38), label, fill=color, font=font_title)
        draw.text((x + 18, y + 95), sub, fill="#a0aec0", font=font_sub)

    # Connecting Arrows
    arrows = [
        (275, 295, 325, 295),
        (565, 295, 615, 295),
        (855, 295, 905, 295),
    ]
    for x1, y1, x2, y2 in arrows:
        draw.line([(x1, y1), (x2, y2)], fill="#00f0ff", width=4)
        draw.polygon([(x2 - 10, y2 - 8), (x2, y2), (x2 - 10, y2 + 8)], fill="#00f0ff")

    img.save(output_path, "PNG")
    return output_path


def render_code_card(output_path: str, section_title: str = "") -> str:
    """Renders a syntax-highlighted code block card."""
    W, H = 1200, 600
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = _resolve_font(20, bold=False)

    draw.rectangle([(0, 0), (W, H)], fill="#0f1420", outline="#00f0ff", width=2)
    draw.rectangle([(0, 0), (W, 44)], fill="#1a2236")
    draw.text((30, 12), "python - runtime/kernel.py", fill="#00f0ff", font=font)

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

    start_y = 70
    for text, color in code_lines:
        draw.text((40, start_y), text, fill=color, font=font)
        start_y += 60

    img.save(output_path, "PNG")
    return output_path


def render_metric_card(output_path: str, section_title: str = "") -> str:
    """Renders a telemetric callout metric card with tight vertical spacing."""
    W, H = 1200, 600
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_percent = _resolve_font(72, bold=True)
    font_title = _resolve_font(24, bold=True)
    font_sub = _resolve_font(18, bold=False)

    draw.rectangle([(0, 0), (W, H)], fill="#0f1420", outline="#00f0ff", width=2)

    # Box 1
    draw.rectangle([(80, 100), (540, 500)], fill="#1a2236", outline="#00f0ff", width=3)
    draw.text((120, 150), "0%", fill="#ffea00", font=font_percent)
    draw.text((120, 260), "SILENT STATE DRIFT", fill="#ffffff", font=font_title)
    draw.text((120, 320), "Deterministic Runtime Guarantee", fill="#a0aec0", font=font_sub)

    # Box 2
    draw.rectangle([(660, 100), (1120, 500)], fill="#1a2236", outline="#38a169", width=3)
    draw.text((700, 150), "100%", fill="#38a169", font=font_percent)
    draw.text((700, 260), "AUDIT TRACEABILITY", fill="#ffffff", font=font_title)
    draw.text((700, 320), "Cryptographic MissionRecord", fill="#a0aec0", font=font_sub)

    img.save(output_path, "PNG")
    return output_path
