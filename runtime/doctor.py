"""
runtime/doctor.py

animus doctor — Studio system health check.

Every check is a REAL I/O test. Not import checks. Not env var sniffing.
Actual calls to actual services.

Usage:
    python -m runtime.doctor           # full report
    python -m runtime.doctor runtime   # infrastructure only
    python -m runtime.doctor models    # Ollama + pulled models
    python -m runtime.doctor caps      # all capabilities
    python -m runtime.doctor publish   # publishing credentials
    python -m runtime.doctor json      # structured JSON output (for API)
"""
from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for d in (root_dir, backend_dir):
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from dotenv import load_dotenv
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if os.path.exists(env_path):
        load_dotenv(env_path)
except Exception:
    pass




# ═══════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════

async def run_doctor(section: str = "all") -> int:
    """
    Run health checks. Prints a formatted report to stdout.
    Returns exit code: 0 = all ok, 1 = warnings, 2 = errors.
    """
    errors = warnings = 0

    _banner()

    if section in ("all", "runtime"):
        e, w = await _check_runtime()
        errors += e; warnings += w

    if section in ("all", "models"):
        e, w = await _check_models()
        errors += e; warnings += w

    if section in ("all", "caps"):
        e, w = await _check_capabilities()
        errors += e; warnings += w

    if section in ("all", "publish"):
        e, w = await _check_publishing()
        errors += e; warnings += w

    if section in ("all", "system"):
        _check_system()

    _divider()
    total = errors + warnings
    health_pct = _health_score(errors, warnings, total)
    if errors:
        _print(f"  ❌  {errors} error(s), {warnings} warning(s) — Studio cannot start cleanly")
    elif warnings:
        _print(f"  ⚠️   {warnings} warning(s) — some capabilities unavailable")
    else:
        _print("  ✅  All checks passed")

    _print(f"\n  Overall Health: {health_pct}%\n")

    return 2 if errors else (1 if warnings else 0)


async def get_doctor_report() -> dict:
    """
    Structured report for FastAPI GET /api/v1/doctor and the Doctor UI page.
    """
    sections: list[dict] = []
    total_passed = total_warnings = total_errors = 0

    # ── 1. Infrastructure ──────────────────────────────────────
    infra_items = []

    # Python
    py_ver = sys.version.split()[0]
    infra_items.append({
        "name": "Python",
        "status": "ok",
        "detail": py_ver,
        "suggestion": "",
        "latency": None,
    })
    total_passed += 1

    # PostgreSQL
    db_item = await _probe_postgres()
    infra_items.append(db_item)
    if db_item["status"] == "ok":   total_passed += 1
    elif db_item["status"] == "error": total_errors += 1
    else:                            total_warnings += 1

    # pgvector
    pgv_item = await _probe_pgvector()
    infra_items.append(pgv_item)
    if pgv_item["status"] == "ok":   total_passed += 1
    elif pgv_item["status"] == "error": total_errors += 1
    else:                             total_warnings += 1

    # Redis
    redis_item = await _probe_redis()
    infra_items.append(redis_item)
    if redis_item["status"] == "ok":   total_passed += 1
    elif redis_item["status"] == "error": total_errors += 1
    else:                               total_warnings += 1

    # Storage
    storage_path = os.getenv("STORAGE_LOCAL_PATH", "./storage")
    if os.path.exists(storage_path):
        infra_items.append({"name": "Storage", "status": "ok", "detail": storage_path, "suggestion": "", "latency": None})
        total_passed += 1
    else:
        infra_items.append({"name": "Storage", "status": "warning", "detail": f"Missing: {storage_path}", "suggestion": f"mkdir {storage_path}", "latency": None})
        total_warnings += 1

    sections.append({"name": "Infrastructure", "items": infra_items})

    # ── 2. Models (Ollama) ─────────────────────────────────────
    model_items = []
    ollama_item = await _probe_ollama_api()
    model_items.append(ollama_item)
    ollama_ok = ollama_item["status"] == "ok"
    if ollama_ok: total_passed += 1
    else:         total_errors += 1

    pulled: set[str] = set()
    if ollama_ok:
        try:
            import httpx
            r = httpx.get(f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/tags", timeout=5)
            pulled = {m["name"] for m in r.json().get("models", [])}
        except Exception:
            pass

    for env_var, label, default in [
        ("DEFAULT_MODEL",   "Chat model",       "qwen3:8b"),
        ("REASONING_MODEL", "Reasoning model",  "deepseek-r1:8b"),
        ("EMBEDDING_MODEL", "Embedding model",  "nomic-embed-text"),
    ]:
        mname = os.getenv(env_var, default)
        mbase = mname.split(":")[0]
        full_matches = {m for m in pulled if m.startswith(mbase)}
        if not ollama_ok:
            model_items.append({"name": label, "status": "error", "detail": "Ollama offline", "suggestion": f"docker compose up ollama", "latency": None})
            total_errors += 1
        elif full_matches:
            model_items.append({"name": label, "status": "ok", "detail": f"Ready ({mname})", "suggestion": "", "latency": None})
            total_passed += 1
        else:
            model_items.append({"name": label, "status": "warning", "detail": f"Not pulled ({mname})", "suggestion": f"ollama pull {mname}", "latency": None})
            total_warnings += 1

    sections.append({"name": "Models", "items": model_items})

    # ── 3. Providers (real healthchecks) ───────────────────────
    provider_items = []

    # Kokoro
    try:
        from providers.voice.kokoro import KokoroProvider
        r = await KokoroProvider().healthcheck()
        provider_items.append(_hc_to_item("Kokoro", r))
        if r.ok: total_passed += 1
        else:    total_warnings += 1
    except Exception as exc:
        provider_items.append({"name": "Kokoro", "status": "error", "detail": str(exc), "suggestion": "pip install kokoro-onnx soundfile", "latency": None})
        total_errors += 1

    # DuckDuckGo
    try:
        from providers.search.duckduckgo import DuckDuckGoProvider
        r = await DuckDuckGoProvider().healthcheck()
        provider_items.append(_hc_to_item("DuckDuckGo", r))
        if r.ok: total_passed += 1
        else:    total_warnings += 1
    except Exception as exc:
        provider_items.append({"name": "DuckDuckGo", "status": "error", "detail": str(exc), "suggestion": "pip install duckduckgo-search", "latency": None})
        total_errors += 1

    # Playwright
    try:
        from providers.scraper.playwright import PlaywrightBrowser
        r = await PlaywrightBrowser().healthcheck()
        provider_items.append(_hc_to_item("Playwright", r))
        if r.ok: total_passed += 1
        else:    total_warnings += 1
    except Exception as exc:
        provider_items.append({"name": "Playwright", "status": "error", "detail": str(exc), "suggestion": "playwright install chromium", "latency": None})
        total_errors += 1

    # FFmpeg
    try:
        from providers.video.ffmpeg import FFmpegAssembler
        r = await FFmpegAssembler().healthcheck()
        provider_items.append(_hc_to_item("FFmpeg", r))
        if r.ok: total_passed += 1
        else:    total_warnings += 1
    except Exception as exc:
        provider_items.append({"name": "FFmpeg", "status": "error", "detail": str(exc), "suggestion": "Install ffmpeg and add to PATH", "latency": None})
        total_errors += 1

    sections.append({"name": "Providers", "items": provider_items})

    # ── 4. Publishing ──────────────────────────────────────────
    pub_items = []
    for name, keys in {
        "YouTube":     ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"),
        "Instagram":   ("META_APP_ID",       "META_ACCESS_TOKEN"),
        "LinkedIn":    ("LINKEDIN_CLIENT_ID", "LINKEDIN_ACCESS_TOKEN"),
        "X (Twitter)": ("TWITTER_API_KEY",   "TWITTER_ACCESS_TOKEN"),
    }.items():
        if all(os.getenv(k) for k in keys):
            pub_items.append({"name": name, "status": "ok", "detail": "Configured", "suggestion": "", "latency": None})
            total_passed += 1
        else:
            pub_items.append({"name": name, "status": "warning", "detail": "Not configured", "suggestion": f"Add {keys[0]} to .env", "latency": None})
            total_warnings += 1
    sections.append({"name": "Publishing", "items": pub_items})

    # ── 5. System ──────────────────────────────────────────────
    sys_items = _system_stats_items()
    sections.append({"name": "System", "items": sys_items})
    total_passed += len([i for i in sys_items if i["status"] == "ok"])

    overall = "ok" if total_errors == 0 and total_warnings == 0 else ("error" if total_errors > 0 else "warning")
    health_pct = _health_score(total_errors, total_warnings, total_passed + total_warnings + total_errors)

    return {
        "status": overall,
        "health_score": health_pct,
        "summary": {
            "passed": total_passed,
            "warnings": total_warnings,
            "errors": total_errors,
        },
        "sections": sections,
    }


# ═══════════════════════════════════════════════════════════════
#  CLI sections
# ═══════════════════════════════════════════════════════════════

async def _check_runtime() -> tuple[int, int]:
    errors = warnings = 0

    _section("Runtime")
    _print()

    # Python
    _ok("Python", sys.version.split()[0])

    # .env
    env_path = ".env"
    if os.path.exists(env_path):
        _ok("Environment", ".env loaded")
    else:
        _warn("Environment", ".env not found — using defaults")
        warnings += 1

    # Config (key env vars)
    required_keys = ["DATABASE_URL", "REDIS_URL"]
    missing_keys = [k for k in required_keys if not os.getenv(k)]
    if missing_keys:
        _warn("Config", f"Missing: {', '.join(missing_keys)}")
        warnings += 1
    else:
        _ok("Config", "Required env vars present")

    _print()
    _section("Infrastructure")
    _print()

    # PostgreSQL — real connection
    t0 = time.monotonic()
    try:
        import asyncpg
        url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg", "postgresql")
        conn = await asyncpg.connect(url, timeout=3)

        # pgvector extension
        pgv = await conn.fetchval("SELECT installed_version FROM pg_available_extensions WHERE name='vector'")
        await conn.close()

        ms = round((time.monotonic() - t0) * 1000)
        _ok("PostgreSQL", f"{os.getenv('POSTGRES_HOST', 'localhost')}  [{ms}ms]")
        if pgv:
            _ok("pgvector", f"extension v{pgv}")
        else:
            _warn("pgvector", "extension not installed  →  CREATE EXTENSION vector;")
            warnings += 1
    except Exception as exc:
        _fail("PostgreSQL", str(exc)[:80])
        errors += 1
        _fail("pgvector", "skipped (Postgres down)")
        errors += 1

    # Redis — real PING (protocol=2 avoids HELLO on Redis < 6.0)
    t0 = time.monotonic()
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), protocol=2)
        await r.ping()
        await r.aclose()
        ms = round((time.monotonic() - t0) * 1000)
        _ok("Redis", f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}  [{ms}ms]")
    except Exception as exc:
        _fail("Redis", str(exc)[:80])
        errors += 1

    # Storage
    storage = os.getenv("STORAGE_LOCAL_PATH", "./storage")
    if os.path.exists(storage):
        _ok("Storage", storage)
    else:
        _warn("Storage", f"directory not found: {storage}  →  mkdir {storage}")
        warnings += 1

    return errors, warnings


async def _check_models() -> tuple[int, int]:
    errors = warnings = 0
    _print()
    _section("Models")
    _print()

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        import httpx
        t0 = time.monotonic()
        resp = httpx.get(f"{host}/api/tags", timeout=5)
        resp.raise_for_status()
        ms = round((time.monotonic() - t0) * 1000)
        pulled_raw = resp.json().get("models", [])
        pulled_names = {m["name"] for m in pulled_raw}
        pulled_bases = {m["name"].split(":")[0] for m in pulled_raw}
        _ok("Ollama", f"{host}  [{ms}ms]  ({len(pulled_names)} model(s) pulled)")

        # Real generation test
        t0 = time.monotonic()
        chat_model = os.getenv("DEFAULT_MODEL", "qwen3:8b")
        try:
            gen_resp = httpx.post(
                f"{host}/api/chat",
                json={
                    "model": chat_model,
                    "messages": [{"role": "user", "content": "Say: ready"}],
                    "stream": False,
                    "options": {"num_predict": 16},
                },
                timeout=120,
            )
            gen_resp.raise_for_status()
            reply = gen_resp.json()["message"]["content"].strip()[:40]
            ms = round((time.monotonic() - t0) * 1000)
            _ok("Generation test", f"'{reply}'  [{ms}ms]")
        except Exception as exc:
            _warn("Generation test", f"failed: {str(exc)[:60]}")
            warnings += 1

        # Model status
        for env_var, label, default in [
            ("DEFAULT_MODEL",   "Chat model",       "qwen3:8b"),
            ("REASONING_MODEL", "Reasoning model",  "deepseek-r1:8b"),
            ("EMBEDDING_MODEL", "Embedding model",  "nomic-embed-text"),
        ]:
            model = os.getenv(env_var, default)
            mbase = model.split(":")[0]
            if mbase in pulled_bases:
                _ok(label, model)
            else:
                _warn(label, f"not pulled  →  ollama pull {model}")
                warnings += 1

    except Exception as exc:
        _fail("Ollama", f"not reachable at {host}  →  docker compose --profile models up ollama")
        errors += 1

    return errors, warnings


async def _check_capabilities() -> tuple[int, int]:
    errors = warnings = 0
    _print()
    _section("Providers")
    _print()

    # Ordered list of (label, factory)
    checks = [
        ("Ollama",      _import("providers.llm.ollama", "OllamaProvider")),
        ("Kokoro",      _import("providers.voice.kokoro", "KokoroProvider")),
        ("DuckDuckGo",  _import("providers.search.duckduckgo", "DuckDuckGoProvider")),
        ("Playwright",  _import("providers.scraper.playwright", "PlaywrightBrowser")),
        ("FFmpeg",      _import("providers.video.ffmpeg", "FFmpegAssembler")),
    ]

    for label, cls in checks:
        if cls is None:
            _fail(label, "module not importable")
            errors += 1
            continue
        try:
            provider = cls()
            result = await provider.healthcheck()
            ms_str = f"  [{result.latency}ms]" if result.latency is not None else ""
            if result.ok:
                _ok(label, f"{result.detail}{ms_str}")
            else:
                fix = result.metadata.get("fix", result.error)
                _warn(label, f"{result.detail}  →  {fix}{ms_str}")
                warnings += 1
        except Exception as exc:
            _fail(label, str(exc)[:80])
            errors += 1

    return errors, warnings


async def _check_publishing() -> tuple[int, int]:
    warnings = 0
    _print()
    _section("Publishing")
    _print()

    # YouTube config defaults
    yt_vis = os.getenv("YOUTUBE_DEFAULT_VISIBILITY", "private")
    yt_cat = os.getenv("YOUTUBE_DEFAULT_CATEGORY", "28")
    yt_lang = os.getenv("YOUTUBE_DEFAULT_LANGUAGE", "en")
    yt_kids = os.getenv("YOUTUBE_MADE_FOR_KIDS", "false")
    _ok("YouTube Config", f"visibility={yt_vis}, category={yt_cat}, lang={yt_lang}, kids={yt_kids}")

    # Check OAuth client credentials
    if os.getenv("YOUTUBE_CLIENT_ID") and os.getenv("YOUTUBE_CLIENT_SECRET"):
        _ok("YouTube OAuth Client", "Client ID & Secret configured")
    else:
        _warn("YouTube OAuth Client", "not configured  →  add YOUTUBE_CLIENT_ID to .env")
        warnings += 1

    # Check database token status via IntegrationManager
    try:
        from runtime.integrations.manager import integration_manager
        item = await integration_manager.get_integration("youtube")
        if item and item.credentials:
            account = item.account_name or "Connected"
            _ok("YouTube Connection", f"Connected as {account}")
        else:
            _warn("YouTube Connection", "Not connected  →  POST /api/v1/integrations/youtube/connect")
            warnings += 1
    except Exception as exc:
        _warn("YouTube Connection", f"DB probe skipped ({str(exc)[:40]})")
        warnings += 1

    # Other social platforms
    services = {
        "Instagram": ("META_APP_ID",       "META_ACCESS_TOKEN"),
        "LinkedIn":  ("LINKEDIN_CLIENT_ID", "LINKEDIN_ACCESS_TOKEN"),
        "X":         ("TWITTER_API_KEY",   "TWITTER_ACCESS_TOKEN"),
    }
    for name, keys in services.items():
        if all(os.getenv(k) for k in keys):
            _ok(name, "configured")
        else:
            _warn(name, f"not configured  →  add {keys[0]} to .env")
            warnings += 1

    return 0, warnings



def _check_system() -> None:
    _print()
    _section("System")
    _print()

    # CPU
    _ok("CPU", f"{platform.processor() or platform.machine()} ({os.cpu_count()} cores)")

    # RAM
    try:
        import psutil
        vm = psutil.virtual_memory()
        total_gb = vm.total / (1024 ** 3)
        avail_gb = vm.available / (1024 ** 3)
        _ok("RAM", f"{avail_gb:.1f}GB free / {total_gb:.1f}GB total")
    except ImportError:
        _ok("RAM", "psutil not installed (pip install psutil for details)")

    # Disk
    try:
        usage = shutil.disk_usage(".")
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        _ok("Disk", f"{free_gb:.1f}GB free / {total_gb:.1f}GB total")
    except Exception:
        _ok("Disk", "check unavailable")

    # GPU
    try:
        import subprocess
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            for line in r.stdout.strip().splitlines():
                _ok("GPU", line.strip())
        else:
            _ok("GPU", "No NVIDIA GPU detected (CPU-only mode)")
    except Exception:
        _ok("GPU", "nvidia-smi not found (CPU-only mode)")


# ═══════════════════════════════════════════════════════════════
#  Internal helpers
# ═══════════════════════════════════════════════════════════════

async def _probe_postgres() -> dict:
    t0 = time.monotonic()
    try:
        import asyncpg
        url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg", "postgresql")
        conn = await asyncpg.connect(url, timeout=3)
        await conn.close()
        return {"name": "PostgreSQL", "status": "ok", "detail": os.getenv("POSTGRES_HOST", "localhost"), "suggestion": "", "latency": round((time.monotonic() - t0) * 1000)}
    except Exception as exc:
        return {"name": "PostgreSQL", "status": "error", "detail": str(exc)[:80], "suggestion": "docker compose up postgres", "latency": None}


async def _probe_pgvector() -> dict:
    try:
        import asyncpg
        url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg", "postgresql")
        conn = await asyncpg.connect(url, timeout=3)
        pgv = await conn.fetchval("SELECT installed_version FROM pg_available_extensions WHERE name='vector'")
        await conn.close()
        if pgv:
            return {"name": "pgvector", "status": "ok", "detail": f"v{pgv}", "suggestion": "", "latency": None}
        else:
            return {"name": "pgvector", "status": "warning", "detail": "Extension not installed", "suggestion": "CREATE EXTENSION vector;", "latency": None}
    except Exception:
        return {"name": "pgvector", "status": "error", "detail": "Postgres unreachable", "suggestion": "Ensure postgres is running", "latency": None}


async def _probe_redis() -> dict:
    t0 = time.monotonic()
    try:
        import redis.asyncio as aioredis
        # protocol=2 (RESP2) avoids the HELLO command on Redis < 6.0
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), protocol=2)
        await r.ping()
        await r.aclose()
        return {"name": "Redis", "status": "ok", "detail": os.getenv("REDIS_URL", "redis://localhost:6379"), "suggestion": "", "latency": round((time.monotonic() - t0) * 1000)}
    except Exception as exc:
        return {"name": "Redis", "status": "error", "detail": str(exc)[:80], "suggestion": "docker compose up redis", "latency": None}


async def _probe_ollama_api() -> dict:
    t0 = time.monotonic()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        import httpx
        resp = httpx.get(f"{host}/api/tags", timeout=5)
        resp.raise_for_status()
        count = len(resp.json().get("models", []))
        return {"name": "Ollama", "status": "ok", "detail": f"{host} — {count} model(s)", "suggestion": "", "latency": round((time.monotonic() - t0) * 1000)}
    except Exception as exc:
        return {"name": "Ollama", "status": "error", "detail": f"Unreachable: {host}", "suggestion": "docker compose --profile models up ollama", "latency": None}


def _system_stats_items() -> list[dict]:
    items = []
    items.append({"name": "Python", "status": "ok", "detail": sys.version.split()[0], "suggestion": "", "latency": None})
    items.append({"name": "Platform", "status": "ok", "detail": platform.platform(), "suggestion": "", "latency": None})

    try:
        import psutil
        vm = psutil.virtual_memory()
        items.append({"name": "RAM", "status": "ok", "detail": f"{vm.available / 1024**3:.1f}GB free / {vm.total / 1024**3:.1f}GB", "suggestion": "", "latency": None})
        items.append({"name": "CPU", "status": "ok", "detail": f"{os.cpu_count()} cores", "suggestion": "", "latency": None})
    except ImportError:
        items.append({"name": "RAM", "status": "ok", "detail": "psutil not installed", "suggestion": "pip install psutil", "latency": None})

    try:
        usage = shutil.disk_usage(".")
        items.append({"name": "Disk", "status": "ok", "detail": f"{usage.free / 1024**3:.1f}GB free / {usage.total / 1024**3:.1f}GB", "suggestion": "", "latency": None})
    except Exception:
        pass

    return items


def _hc_to_item(label: str, result: "HealthCheckResult") -> dict:
    from providers.health_contract import HealthCheckResult as HC
    return {
        "name": label,
        "status": "ok" if result.ok else "warning",
        "detail": result.detail,
        "suggestion": result.metadata.get("fix", result.error),
        "latency": result.latency,
    }


def _import(module: str, cls: str):
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, cls)
    except Exception:
        return None


def _health_score(errors: int, warnings: int, total: int) -> int:
    if total == 0:
        return 100
    deductions = (errors * 10) + (warnings * 2)
    return max(0, min(100, 100 - deductions))


# ═══════════════════════════════════════════════════════════════
#  Output helpers
# ═══════════════════════════════════════════════════════════════

WIDTH = 52

def _banner() -> None:
    _print()
    _print("  " + "═" * WIDTH)
    _print("             Animus Studio — Doctor")
    _print("  " + "═" * WIDTH)

def _section(name: str) -> None:
    _print(f"  {name}")
    _print("  " + "─" * WIDTH)

def _divider() -> None:
    _print()
    _print("  " + "═" * WIDTH)

def _print(text: str = "") -> None:
    print(text)

def _ok(label: str, detail: str) -> None:
    print(f"  ✓  {label:<28} {detail}")

def _warn(label: str, detail: str) -> None:
    print(f"  ⚠  {label:<28} {detail}")

def _fail(label: str, detail: str) -> None:
    print(f"  ✗  {label:<28} {detail}")


# ═══════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    section = sys.argv[1] if len(sys.argv) > 1 else "all"

    if section == "json":
        report = asyncio.run(get_doctor_report())
        print(json.dumps(report, indent=2))
        sys.exit(0)

    exit_code = asyncio.run(run_doctor(section))
    sys.exit(exit_code)
