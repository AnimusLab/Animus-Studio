"""
agents/editor/motion_bg.py

Procedural Motion Background Engine.
Generates ANIMATED video backgrounds — not static images. Every frame is different.

Each background is thematically tied to the video section:
  "terminal_crash"   → Scrolling red error cascade    (Section 1: The Problem)
  "network_topology" → Animated connecting node graph  (Section 2: Architecture)
  "code_stream"      → Multi-column scrolling code     (Section 3: The Solution)
  "particle_vortex"  → Orbiting gold particle shield   (Section 4: Governance)

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
from PIL import Image, ImageDraw

W, H = 1920, 1080

# ── Font Cache (loaded once, reused across frames) ──────────────────────────

_FONT_CACHE: dict = {}


def _font(size: int, mono: bool = True):
    key = (size, mono)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    from PIL import ImageFont
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
#  SECTION 2 — Animated Network Topology
#  Glowing nodes appearing, connecting with pulsing edges, data packets
#  travelling along edges. Cyan/blue on very dark navy.
#  Thematic link: AI agent architecture — the system design under the hood.
# ═══════════════════════════════════════════════════════════════════════════

# Pre-compute stable node positions once (seeded so deterministic)
_rng_nodes = random.Random(1337)
_NODES: list[tuple[int, int]] = [
    (_rng_nodes.randint(180, W - 180), _rng_nodes.randint(140, H - 140))
    for _ in range(28)
]
_NODE_LABELS = [
    "KERNEL", "AGENT", "LLM", "AUDIT", "STATE", "MEMORY",
    "POLICY", "GUARD", "EXEC", "LOG", "MONITOR", "ROUTER",
    "INPUT", "OUTPUT", "PLAN", "TOOL", "SANDBOX", "VERIFY",
    "HASH", "SIGN", "REPLAY", "TRACE", "SCOPE", "SYNC",
    "QUEUE", "LOCK", "TIMEOUT", "ROLLBACK",
]
# Pre-compute which nodes connect (edges)
_rng_edges = random.Random(2024)
_EDGES: list[tuple[int, int]] = []
for _i in range(len(_NODES)):
    for _j in range(_i + 1, len(_NODES)):
        nx1, ny1 = _NODES[_i]
        nx2, ny2 = _NODES[_j]
        dist = math.hypot(nx2 - nx1, ny2 - ny1)
        if dist < 310 and _rng_edges.random() < 0.45:
            _EDGES.append((_i, _j))


def network_topology_bg(t: float) -> np.ndarray:
    """Animated network topology — pulsing nodes, animated data-packet edges."""
    img = Image.new("RGB", (W, H), (3, 6, 16))
    draw = ImageDraw.Draw(img)
    f_tiny = _font(13, mono=True)

    # Draw edges with animated data packets
    for ei, (ni, nj) in enumerate(_EDGES):
        x1, y1 = _NODES[ni]
        x2, y2 = _NODES[nj]

        # Edge phase unique to this edge
        edge_phase = (t * 0.7 + ei * 0.23) % 1.0
        # Base line colour — dim cyan
        draw.line([(x1, y1), (x2, y2)], fill=(15, 55, 80), width=1)

        # Animated bright packet travelling along edge
        px = int(x1 + (x2 - x1) * edge_phase)
        py = int(y1 + (y2 - y1) * edge_phase)
        pkt_r = 4
        draw.ellipse(
            [(px - pkt_r, py - pkt_r), (px + pkt_r, py + pkt_r)],
            fill=(0, 210, 255),
        )

    # Draw nodes — pulsing circles
    for idx, (nx, ny) in enumerate(_NODES):
        pulse = 0.5 + 0.5 * math.sin(t * 1.2 + idx * 0.7)
        r = int(6 + pulse * 5)
        # Outer glow ring
        glow_r = r + 8
        draw.ellipse(
            [(nx - glow_r, ny - glow_r), (nx + glow_r, ny + glow_r)],
            fill=(0, 40, 70),
        )
        # Node core
        draw.ellipse(
            [(nx - r, ny - r), (nx + r, ny + r)],
            fill=(0, 180, 240),
        )
        # Label
        label = _NODE_LABELS[idx % len(_NODE_LABELS)]
        draw.text((nx + r + 5, ny - 8), label, fill=(0, 140, 190), font=f_tiny)

    # Subtle horizontal scan lines
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for ys in range(1, H, 5):
        sd.rectangle([(0, ys), (W, ys + 1)], fill=(0, 0, 0, 35))
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
#  SECTION 4 — Particle Vortex (Governance Shield)
#  Gold/amber particles orbiting a glowing core, forming layered rings.
#  Thematic link: Security, deterministic governance, protection.
# ═══════════════════════════════════════════════════════════════════════════

# Pre-compute stable particle orbits
_rng_p = random.Random(9999)
_N_PARTICLES = 180
_P_RADIUS  = [_rng_p.uniform(160, 420) for _ in range(_N_PARTICLES)]
_P_PHASE   = [_rng_p.uniform(0, 2 * math.pi) for _ in range(_N_PARTICLES)]
_P_SPEED   = [_rng_p.uniform(0.18, 0.55) for _ in range(_N_PARTICLES)]   # rad/s
_P_SIZE    = [_rng_p.randint(2, 6) for _ in range(_N_PARTICLES)]
_P_BRIGHT  = [_rng_p.uniform(0.4, 1.0) for _ in range(_N_PARTICLES)]
_CX, _CY   = W // 2, H // 2


def particle_vortex_bg(t: float) -> np.ndarray:
    """Orbiting gold/amber particle rings — protective governance shield."""
    img = Image.new("RGB", (W, H), (3, 3, 8))
    draw = ImageDraw.Draw(img)

    # Core glow — layered concentric ellipses
    for glow_r, alpha_frac in [(140, 0.06), (80, 0.12), (40, 0.22), (18, 0.5)]:
        glow_col = (
            int(255 * alpha_frac),
            int(165 * alpha_frac * 0.7),
            int(10 * alpha_frac),
        )
        draw.ellipse(
            [(_CX - glow_r, _CY - glow_r), (_CX + glow_r, _CY + glow_r)],
            fill=glow_col,
        )

    # Orbital rings (faint guide circles)
    for ring_r in [180, 280, 380]:
        draw.ellipse(
            [
                (_CX - ring_r, _CY - ring_r * 0.38),
                (_CX + ring_r, _CY + ring_r * 0.38),
            ],
            outline=(60, 45, 10),
            width=1,
        )

    # Particles
    for i in range(_N_PARTICLES):
        angle = _P_PHASE[i] + _P_SPEED[i] * t
        r = _P_RADIUS[i]
        # Isometric orbit (elliptical projection)
        px = _CX + r * math.cos(angle)
        py = _CY + r * 0.38 * math.sin(angle)
        br = _P_BRIGHT[i]
        sz = _P_SIZE[i]
        # Gold/amber particle colour
        col = (
            int(255 * br),
            int(185 * br * 0.75),
            int(20 * br * 0.3),
        )
        draw.ellipse(
            [(px - sz, py - sz), (px + sz, py + sz)],
            fill=col,
        )

    # Slow rotation shimmer overlay
    shimmer_phase = (t * 0.15) % 1.0
    shimmer_y = int(shimmer_phase * H)
    shim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shim)
    sd.rectangle([(0, shimmer_y - 2), (W, shimmer_y + 2)], fill=(255, 200, 60, 12))
    img = Image.alpha_composite(img.convert("RGBA"), shim).convert("RGB")

    return _np(img)


# ═══════════════════════════════════════════════════════════════════════════
#  Pre-render Engine — pipes frames to ffmpeg, returns path to MP4
# ═══════════════════════════════════════════════════════════════════════════

_BG_FNS = {
    "terminal_crash":   terminal_crash_bg,
    "network_topology": network_topology_bg,
    "code_stream":      code_stream_bg,
    "particle_vortex":  particle_vortex_bg,
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

    Args:
        bg_type: One of "terminal_crash", "network_topology", "code_stream", "particle_vortex"
        duration: Length in seconds.
        output_path: Destination .mp4 path.
        fps: Frames per second (24 recommended).
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
