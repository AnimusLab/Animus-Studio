"""
providers/health_contract.py

Shared HealthCheckResult type and BaseHealthCheck mixin.

Every provider that implements healthcheck() must return a HealthCheckResult.
This is the contract. Nothing else.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HealthCheckResult:
    """
    Returned by every provider.healthcheck() call.

    ok       — did the real I/O test pass?
    name     — provider identifier
    detail   — human-readable status line
    latency  — milliseconds, None if not measured
    metadata — extra k/v for display (model name, URL, version, etc.)
    error    — exception message if ok is False
    """
    ok:       bool
    name:     str
    detail:   str
    latency:  float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error:    str = ""


class HealthCheckMixin:
    """
    Mixin that providers inherit to get a standard healthcheck() signature.
    Subclasses must override _healthcheck().
    """

    async def healthcheck(self) -> HealthCheckResult:
        """
        Run the real I/O health test.
        Returns HealthCheckResult — never raises.
        """
        import time
        t0 = time.monotonic()
        try:
            result = await self._healthcheck()
            result.latency = round((time.monotonic() - t0) * 1000)
            return result
        except Exception as exc:
            return HealthCheckResult(
                ok=False,
                name=getattr(self, "name", type(self).__name__),
                detail="healthcheck raised an exception",
                latency=round((time.monotonic() - t0) * 1000),
                error=str(exc),
            )

    async def _healthcheck(self) -> HealthCheckResult:
        """Override this. Perform a real I/O test. Return HealthCheckResult."""
        return HealthCheckResult(
            ok=self.is_available() if hasattr(self, "is_available") else True,
            name=getattr(self, "name", type(self).__name__),
            detail="is_available() check (no I/O override)",
        )
