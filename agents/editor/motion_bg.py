"""
agents/editor/motion_bg.py

Procedural Motion Background Engine.
Generates ANIMATED video backgrounds — not static images. Every frame is different.

Each background is thematically tied to the video section:
  "terminal_crash"   → Scrolling red error cascade    (Section 1: The Problem)
  "lidar_radar"      → Lidar Sweep / Self-Driving Car (Section 2: Architecture & Self-Driving analogy)
  "code_stream"      → Multi-column scrolling code     (Section 3: The Solution)
  "cryptographic_ledger" → Verified Governance Chain  (Section 4: Governance & Transparency)

Usage:
    path = pre_render_bg_mp4("terminal_crash", duration=15.0, output_path="bg1.mp4")
    # Returns path to an MP4 usable as VideoFileClip in MoviePy.
"""
from __future__ import annotations

import math
import os
import subprocess
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080

# ── Font Cache (loaded once, reused across frames) ──────────────────────────

_FONT_CACHE: dict = {}


def _font(size: int, mono: bool = True):
    key = (size, mono)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    paths = (
        [
            r"C:\Windows\Fonts\consola.ttf",
            r"C:\Windows\Fonts\cour.ttf",
            r"C:\Windows\Fonts\lucon.ttf",
        ]
        if mono else
        [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
    )
    f = ImageFont.load_default()
    for p in paths:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, size)
                break
            except Exception:
                pass
    _FONT_CACHE[key] = f
    return f


def _np(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 1 — Terminal Error Cascade
#  Dark background, red cascading kernel panic / AI failure error messages.
#  Thematic link: AI systems failing in production without governance.
# ═══════════════════════════════════════════════════════════════════════════

_CRASH_LINES = [
    "KERNEL PANIC: AI state corruption detected at 0x7fff3a2b4c01",
    "FATAL: Runtime governance check FAILED — execution halted",
    "ERROR [0x4f]: LLM output diverged from deterministic specification",
    "[CRITICAL] audit_log.write() — permission denied: orphaned context",
    "Traceback: agents.kernel.StateError: rollback failed at checkpoint",
    "WARN: 847 silent model failures detected in last 24-hour window",
    ">> Production pipeline OFFLINE — root cause undetermined",
    "ERROR: MissionRecord.commit() — cryptographic signature mismatch",
    "KERNEL FAULT: Memory violation @ agent_executor.py:line 482",
    "sys: governed_stream diverged — force-truncating execution context",
    "CRITICAL: agent loop escape detected — isolation boundary breached",
    "RuntimeError: deterministic delta=0.847 exceeds tolerance threshold",
    "FATAL: telemetry pipeline disconnected — audit trail BROKEN",
    "[ERROR] state_lock.acquire() timeout after 30.0s — deadlock suspected",
    "PANIC: emergency rollback failed — state irrecoverably corrupted",
    "ERROR: cryptographic verification mismatch on governed output stream",
    "WARN: nondeterministic output detected in production mission kernel",
    "FATAL: AI agent produced undocumented side effects — quarantining",
]


def terminal_crash_bg(t: float) -> np.ndarray:
    """Red cascading terminal error output scrolling top-to-bottom."""
    img = Image.new("RGB", (W, H), (5, 8, 14))
    draw = ImageDraw.Draw(img)

    f_lg = _font(20, mono=True)

    line_h = 33
    scroll_speed = 70  # px/s — feels like a live crash dump
    scroll_y = (t * scroll_speed) % (len(_CRASH_LINES) * line_h)

    n = len(_CRASH_LINES)
    repeats = H // (n * line_h) + 3

    for rep in range(repeats):
        for i, line in enumerate(_CRASH_LINES):
            y = rep * n * line_h + i * line_h - scroll_y
            if not (-line_h <= y <= H + line_h):
                continue
            # Colour by severity
            if any(k in line for k in ("FATAL", "CRITICAL", "PANIC")):
                r, g, b = 255, 28, 28
            elif "ERROR" in line:
                r, g, b = 215, 60, 35
            elif "WARN" in line:
                r, g, b = 210, 120, 25
            else:
                r, g, b = 130, 30, 30
            # Fade toward edges vertically
            fade = max(0.12, 1.0 - abs(y - H * 0.5) / (H * 0.55))
            col = (int(r * fade), int(g * fade), int(b * fade))
            draw.text((80, int(y)), line, fill=col, font=f_lg)

    # Scanline overlay
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for ys in range(1, H, 4):
        sd.rectangle([(0, ys), (W, ys + 1)], fill=(0, 0, 0, 55))
    img = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

    # Blinking cursor bottom-left
    draw2 = ImageDraw.Draw(img)
    if int(t * 1.5) % 2 == 0:
        draw2.text((80, H - 90), ">> _", fill=(255, 35, 35), font=f_lg)

    # Periodic red glitch flash
    if (t % 9.0) < 0.07:
        arr = np.array(img, dtype=np.float32)
        arr[:, :, 0] = np.minimum(255, arr[:, :, 0] + 18)
        img = Image.fromarray(arr.astype(np.uint8))

    return _np(img)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 2 — Lidar / Radar Scanner (Autonomous Vehicle Grid)
#  Concentric circles, rotating scanner sweep, lane indicators, and boxes
#  with labels (CAR, PEDESTRIAN) that highlight as the sweep passes.
#  Thematic link: Autonomous vehicles / self-driving cars narration analogy.
# ═══════════════════════════════════════════════════════════════════════════

# Center coordinates
_CX, _CY = W // 2, H // 2

# Stable obstacle positions relative to center (dx, dy, width, height, label)
_OBSTACLES = [
    (-350, -180, 70, 110, "VEHICLE_A [V2X]"),
    (280, -220, 60, 95,   "VEHICLE_B [ACTIVE]"),
    (-220, 140, 30, 60,   "PEDESTRIAN_A [0.98]"),
    (180, 200, 35, 55,    "PEDESTRIAN_B [0.94]"),
    (-500, 80, 90, 140,   "TRUCK [DIST: 42m]"),
    (480, 110, 55, 80,    "CYCLIST [0.91]"),
]


def lidar_radar_bg(t: float) -> np.ndarray:
    """Lidar radar sweep scanner with bounding boxes & lane indicators."""
    img = Image.new("RGB", (W, H), (2, 8, 16))
    draw = ImageDraw.Draw(img)

    f_lbl = _font(13, mono=True)
    f_num = _font(15, mono=True)

    # 1. Concentric sweep circular guides
    for r in [120, 250, 380, 520]:
        draw.ellipse([(_CX - r, _CY - r), (_CX + r, _CY + r)], outline=(12, 45, 65), width=1)

    # 2. Coordinate lines (crosshairs)
    draw.line([(0, _CY), (W, _CY)], fill=(12, 45, 65), width=1)
    draw.line([(_CX, 0), (_CX, H)], fill=(12, 45, 65), width=1)

    # 3. Rotating sweep line (1.4 rad/s)
    sweep_rad = (t * 1.3) % (2 * math.pi)
    sx = int(_CX + 600 * math.cos(sweep_rad))
    sy = int(_CY + 600 * math.sin(sweep_rad))
    draw.line([(_CX, _CY), (sx, sy)], fill=(0, 220, 255, 120), width=2)

    # 4. Animated sweep trail glow
    trail_steps = 15
    for step in range(trail_steps):
        angle = sweep_rad - (step * 0.04)
        alpha = int(75 * (1.0 - step / trail_steps))
        tx = int(_CX + 600 * math.cos(angle))
        ty = int(_CY + 600 * math.sin(angle))
        draw.line([(_CX, _CY), (tx, ty)], fill=(0, 180, 220, alpha), width=1)

    # 5. Autonomous lane boundary guides (angled vectors representing perspective)
    draw.line([(_CX - 50, _CY + 40), (_CX - 350, H)], fill=(0, 90, 130), width=1)
    draw.line([(_CX + 50, _CY + 40), (_CX + 350, H)], fill=(0, 90, 130), width=1)

    # 6. Obstacle boxes with sweep angle illumination
    for idx, (dx, dy, box_w, box_h, label) in enumerate(_OBSTACLES):
        ox, oy = _CX + dx, _CY + dy
        obs_angle = math.atan2(dy, dx)
        if obs_angle < 0:
            obs_angle += 2 * math.pi

        # Compute sweep intersection distance
        angle_diff = abs(sweep_rad - obs_angle)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff

        # Decaying activation value based on how recently the sweep line passed
        activation = max(0.15, 1.0 - (angle_diff * 1.5))

        # Color shifts from cyan (active sweep) to dark teal (idle)
        r_box = int(0 * activation + 10 * (1 - activation))
        g_box = int(240 * activation + 60 * (1 - activation))
        b_box = int(255 * activation + 90 * (1 - activation))
        box_col = (r_box, g_box, b_box)

        # Draw bounding box
        draw.rectangle(
            [(ox - box_w // 2, oy - box_h // 2), (ox + box_w // 2, oy + box_h // 2)],
            outline=box_col,
            width=2,
        )

        # Draw tech crosshairs on bounding corners
        ch = 8
        bx1, by1 = ox - box_w // 2, oy - box_h // 2
        bx2, by2 = ox + box_w // 2, oy + box_h // 2
        # Top Left
        draw.line([(bx1 - 3, by1), (bx1 + ch, by1)], fill=(0, 255, 255), width=1)
        draw.line([(bx1, by1 - 3), (bx1, by1 + ch)], fill=(0, 255, 255), width=1)
        # Bottom Right
        draw.line([(bx2 + 3, by2), (bx2 - ch, by2)], fill=(0, 255, 255), width=1)
        draw.line([(bx2, by2 + 3), (bx2, by2 - ch)], fill=(0, 255, 255), width=1)

        # Label text
        draw.text(
            (ox - box_w // 2, oy - box_h // 2 - 20),
            label,
            fill=box_col,
            font=f_lbl,
        )

    # 7. Sweep telemetry details (top left)
    draw.text((80, 80), "LIDAR SCANNING: ACTIVE", fill=(0, 240, 255), font=f_num)
    draw.text((80, 105), f"SWEEP_RAD: {sweep_rad:.4f} RAD", fill=(0, 180, 220), font=f_num)
    draw.text((80, 130), f"OBJECTS DETECTED: {len(_OBSTACLES)} UNITS", fill=(0, 180, 220), font=f_num)

    # Horizontal scanner grid lines
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for ys in range(1, H, 5):
        sd.rectangle([(0, ys), (W, ys + 1)], fill=(0, 0, 0, 40))
    img = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

    return _np(img)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 3 — Code Stream
#  Multiple columns of scrolling code at different speeds. Syntax-coloured
#  Python resembling actual Animus runtime kernel code.
#  Thematic link: The solution — real implementation, running kernel code.
# ═══════════════════════════════════════════════════════════════════════════

_CODE_LINES = [
    ("@kernel.governed(name='production_pipeline')", "decorator"),
    ("async def run_governed_agent(spec: MissionSpec):", "def"),
    ("    # 1. Acquire deterministic state lock", "comment"),
    ("    ctx = await runtime.acquire_state_lock(spec)", "code"),
    ("    # 2. Execute LLM decision with audit capture", "comment"),
    ("    result = await llm.chat_with_provenance(ctx)", "code"),
    ("    # 3. Cryptographically sign execution record", "comment"),
    ("    return await MissionRecord.commit(result)", "return"),
    ("", "blank"),
    ("class MissionRecord:", "class"),
    ("    async def commit(cls, result: AgentOutput):", "def"),
    ("        sig = hmac.sign(result.hash, key=SECRET)", "code"),
    ("        await db.insert_record(result, sig)", "code"),
    ("        await telemetry.emit('mission.complete')", "code"),
    ("        return result", "return"),
    ("", "blank"),
    ("@state_machine.transition(from_='running')", "decorator"),
    ("def on_governed_output(self, output):", "def"),
    ("    if not self.validator.check(output):", "code"),
    ("        raise StateError('output diverged')", "raise"),
    ("    self.audit_log.append(output)", "code"),
    ("    self.state = 'completed'", "code"),
    ("", "blank"),
    ("# Runtime provenance pipeline", "comment"),
    ("async def stream_with_audit(prompt, ctx):", "def"),
    ("    async for token in llm.stream(prompt):", "code"),
    ("        ctx.provenance.record(token)", "code"),
    ("        yield token", "code"),
    ("", "blank"),
    ("class DeterministicKernel:", "class"),
    ("    def __init__(self, policy: GovernancePolicy):", "def"),
    ("        self.policy = policy", "code"),
    ("        self.state_lock = asyncio.Lock()", "code"),
    ("", "blank"),
]

# Colour scheme (R,G,B)
_CODE_COLOURS = {
    "decorator": (180, 100, 255),
    "def":       (80,  150, 255),
    "class":     (80,  200, 130),
    "comment":   (80,  110, 80),
    "code":      (200, 210, 220),
    "return":    (255, 130, 100),
    "raise":     (255, 80,  80),
    "blank":     (0,   0,   0),
}

# 3 columns with different speeds
_COL_X       = [60,  700, 1340]
_COL_SPEEDS  = [55,  40,  70]   # px/s scroll speed per column
_COL_OFFSETS = [0,   len(_CODE_LINES) // 3,  2 * len(_CODE_LINES) // 3]


def code_stream_bg(t: float) -> np.ndarray:
    """Multi-column scrolling Python code — teal/cyan on near-black."""
    img = Image.new("RGB", (W, H), (4, 6, 10))
    draw = ImageDraw.Draw(img)
    f = _font(18, mono=True)

    line_h = 28

    for col_i, (cx, speed, offset) in enumerate(
        zip(_COL_X, _COL_SPEEDS, _COL_OFFSETS)
    ):
        scroll_y = (t * speed + offset * line_h) % (len(_CODE_LINES) * line_h)
        n = len(_CODE_LINES)
        repeats = H // (n * line_h) + 3

        for rep in range(repeats):
            for li, (line_text, line_type) in enumerate(_CODE_LINES):
                y = rep * n * line_h + li * line_h - scroll_y
                if not (-line_h <= y <= H + line_h):
                    continue
                col_base = _CODE_COLOURS.get(line_type, (180, 180, 180))
                # Fade by distance from column centre vertically
                fade = max(0.08, 1.0 - abs(y - H * 0.5) / (H * 0.6))
                col = tuple(int(c * fade) for c in col_base)
                draw.text((cx, int(y)), line_text, fill=col, font=f)

    # Faint column dividers
    for cx in _COL_X[1:]:
        draw.line([(cx - 20, 0), (cx - 20, H)], fill=(20, 30, 25), width=1)

    # Scanlines
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for ys in range(1, H, 4):
        sd.rectangle([(0, ys), (W, ys + 1)], fill=(0, 0, 0, 45))
    img = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

    return _np(img)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 4 — Cryptographic Ledger Chain
#  Glowing blocks displaying commit hashes, verification checkmarks, and
#  active audit logs. Vertical chain link scrolling upwards.
#  Thematic link: Transparency, accountability, and secure auditing.
# ═══════════════════════════════════════════════════════════════════════════

# Pre-computed stable transaction logs
_LEDGER_ITEMS = [
    ("tx_8c2278b", "STATE_LOCK", "SUCCESS", "0.00ms", "0.0% drift"),
    ("tx_4f009a2", "LLM_INFERENCE", "GOVERNED", "482ms", "sha256:8f2a..."),
    ("tx_91227cc", "POLICY_CHECK", "VERIFIED", "1.25ms", "100% compliance"),
    ("tx_7b99a01", "AUDIT_COMMIT", "COMMITTED", "12.0ms", "sig:9f23..."),
    ("tx_3c48f2b", "STATE_ROLLBACK", "BYPASS", "0.00ms", "0.0% drift"),
    ("tx_1a44e6d", "TELEMETRY_EMIT", "VERIFIED", "0.55ms", "active"),
]


def cryptographic_ledger_bg(t: float) -> np.ndarray:
    """Chain of cryptographic ledger blocks with status checks scrolling upward."""
    img = Image.new("RGB", (W, H), (4, 10, 8))
    draw = ImageDraw.Draw(img)

    f_lbl = _font(15, mono=True)
    f_num = _font(17, mono=True)
    f_val = _font(20, mono=True)

    block_h = 130
    block_gap = 40
    total_h = block_h + block_gap
    scroll_speed = 45  # px/s
    scroll_y = (t * scroll_speed) % (len(_LEDGER_ITEMS) * total_h)

    n = len(_LEDGER_ITEMS)
    repeats = H // (n * total_h) + 3

    # Draw vertical chain links behind blocks
    draw.line([(W // 2, 0), (W // 2, H)], fill=(12, 45, 25), width=6)

    for rep in range(repeats):
        for idx, (tx, name, status, lat, extra) in enumerate(_LEDGER_ITEMS):
            y = rep * n * total_h + idx * total_h - scroll_y
            if not (-block_h <= y <= H + block_h):
                continue

            # Draw block frame (concentric transparent check blocks)
            bx1, bx2 = W // 2 - 320, W // 2 + 320
            by1, by2 = int(y), int(y + block_h)

            # Fade block based on screen position
            fade = max(0.12, 1.0 - abs(by1 - H * 0.5) / (H * 0.6))
            border_alpha = int(180 * fade)
            fill_alpha = int(95 * fade)

            # Block background & borders
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            odraw.rounded_rectangle(
                [(bx1, by1), (bx2, by2)],
                radius=8,
                fill=(5, 15, 10, fill_alpha),
                outline=(0, 204, 136, border_alpha),
                width=2,
            )
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)  # Refresh draw context

            # Block details text
            c_text = (int(200 * fade), int(230 * fade), int(210 * fade))
            c_accent = (int(0 * fade), int(230 * fade), int(150 * fade))

            draw.text((bx1 + 25, by1 + 18), f"LEDGER BLOCK // {tx.upper()}", fill=c_text, font=f_num)
            draw.text((bx1 + 25, by1 + 52), f"ACTION: {name}", fill=c_text, font=f_lbl)
            draw.text((bx1 + 25, by1 + 80), f"METRIC: {extra}", fill=c_text, font=f_lbl)

            # Verification stamp (Right side)
            draw.text((bx2 - 200, by1 + 25), f"STATUS: {status}", fill=c_accent, font=f_val)
            draw.text((bx2 - 200, by1 + 65), f"LATENCY: {lat}", fill=c_text, font=f_lbl)

            # Green check shield icon (small bounding box)
            draw.rounded_rectangle(
                [(bx2 - 250, by1 + 35), (bx2 - 220, by1 + 65)],
                radius=4,
                outline=c_accent,
                width=2,
            )
            draw.text((bx2 - 243, by1 + 39), "[OK]", fill=c_accent, font=f_lbl)

    # Telemetry details (top left)
    draw.text((80, 80), "AUDITING TELEMETRY: GOVERNED", fill=(0, 204, 136), font=f_val)
    draw.text((80, 110), "TELEMETRY HASH: SHA-256/ACTIVE", fill=(150, 180, 160), font=f_lbl)

    # Horizontal scanner grid lines
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for ys in range(1, H, 6):
        sd.rectangle([(0, ys), (W, ys + 1)], fill=(0, 0, 0, 35))
    img = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

    return _np(img)


# ═══════════════════════════════════════════════════════════════════════════
#  Pre-render Engine — pipes frames to ffmpeg, returns path to MP4
# ═══════════════════════════════════════════════════════════════════════════

_BG_FNS = {
    "terminal_crash":   terminal_crash_bg,
    "network_topology": lidar_radar_bg,
    "code_stream":      code_stream_bg,
    "particle_vortex":  cryptographic_ledger_bg,
}

# Mapping from section style name (used in cinematic.py) to bg type
STYLE_TO_BG = {
    "server_alert":      "terminal_crash",
    "architecture_blue": "network_topology",
    "code_matrix":       "code_stream",
    "audit_emerald":     "particle_vortex",
}


def pre_render_bg_mp4(
    bg_type: str,
    duration: float,
    output_path: str,
    fps: int = 24,
) -> str:
    """
    Pre-renders an animated background to an MP4 file by piping frames to ffmpeg.
    Returns output_path on success, raises on failure.
    """
    frame_fn = _BG_FNS.get(bg_type)
    if frame_fn is None:
        raise ValueError(f"Unknown bg_type '{bg_type}'. Choose from: {list(_BG_FNS)}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "pipe:",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-crf", "22",
        output_path,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n_frames = int(duration * fps)

    try:
        for fi in range(n_frames):
            t = fi / fps
            frame_arr = frame_fn(t)   # (H, W, 3) uint8
            proc.stdin.write(frame_arr.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()

    if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
        raise RuntimeError(f"motion_bg: ffmpeg failed to produce {output_path}")

    return output_path
