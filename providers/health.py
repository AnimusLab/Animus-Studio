"""
Provider Health Check

Run at startup to print the capability matrix.
Also exposed as GET /api/v1/health/capabilities
"""
from __future__ import annotations
from runtime.capabilities import Capability, CAPABILITY_META
from runtime.registry import runtime


async def run_health_check() -> dict:
    await runtime.bootstrap()
    results = runtime.capabilities.health()

    print("\n" + "═" * 52)
    print("  Animus Studio — Capability Matrix")
    print("═" * 52)

    for cap in Capability:
        meta   = CAPABILITY_META.get(cap, {})
        result = results.get(cap, {})
        status = result.get("status", "unavailable")
        provider = result.get("provider", "")
        model    = result.get("model", "")

        icon   = "✅" if status == "ok" else "❌"
        detail = f"{provider}/{model}" if model else provider or "—"
        label  = meta.get("label", cap.value).ljust(22)

        print(f"  {icon}  {label}  {detail}")
        if status != "ok":
            suggest = meta.get("suggest", "")
            if suggest:
                print(f"        Suggestion: {suggest}")

    print("═" * 52 + "\n")
    return results
