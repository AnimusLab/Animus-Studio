"""
runtime/context.py

Three-layer context model. See ARCHITECTURE_v1.md.

RuntimeContext  — stable, never changes (the runtime itself)
MissionSpec     — immutable mission specification
ExecutionContext — mutable execution state per run
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from runtime.registry import Runtime


@dataclass(frozen=True)
class RuntimeContext:
    """
    Stable. Set once at startup. Never mutated.
    Carries the kernel and config.
    """
    runtime: "Runtime"
    config:  Any                          # app Settings
    logger:  Any = field(default=None)    # structlog BoundLogger

    def __post_init__(self) -> None:
        if self.logger is None:
            object.__setattr__(self, "logger", structlog.get_logger())


@dataclass(frozen=True)
class MissionSpec:
    """
    Immutable. Set once per mission. The specification of intent.
    Workers read this but never modify it.
    """
    mission_id:  str
    goal:        str
    brand_id:    str
    brand_name:  str
    audience:    str = "general"
    language:    str = "en"
    tone:        str = "professional"
    deadline:    datetime | None = None
    metadata:    dict = field(default_factory=dict)

    @classmethod
    def from_mission(cls, mission: Any, brand: Any) -> "MissionSpec":
        """Build from DB mission + brand objects."""
        return cls(
            mission_id=str(mission.id),
            goal=mission.goal,
            brand_id=str(brand.id),
            brand_name=brand.name,
            audience=getattr(brand, "target_audience", "general"),
            language=getattr(mission, "language", "en"),
            tone=getattr(brand, "tone", "professional"),
            deadline=getattr(mission, "deadline", None),
            metadata=getattr(mission, "metadata", {}),
        )


@dataclass
class ExecutionContext:
    """
    Mutable. One per workflow execution.
    All worker outputs live in `artifacts`.
    Workers never pass data between themselves directly — only via artifacts.
    """
    execution_id:  str
    step:          str = ""
    retry_count:   int = 0
    artifacts:     dict = field(default_factory=dict)
    _events:       Any  = field(default=None, repr=False)     # EventBus
    cancellation:  asyncio.Event = field(default_factory=asyncio.Event)

    # ── Artifact access ───────────────────────────────────────
    def get(self, key: str, default: Any = None) -> Any:
        return self.artifacts.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.artifacts[key] = value

    def has(self, key: str) -> bool:
        return key in self.artifacts

    # ── Event emission ────────────────────────────────────────
    def emit(self, event_type: str, payload: dict | None = None) -> None:
        """Emit a step event. Non-blocking."""
        if self._events is None:
            return
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(
                    self._events.emit(
                        event_type=event_type,
                        step=self.step,
                        payload=payload or {},
                    )
                )
        except Exception:
            pass     # event emission never breaks execution

    def step_started(self, worker: str) -> None:
        self.step = worker
        self.emit("step.started", {"worker": worker, "retry": self.retry_count})

    def step_completed(self, worker: str, output_keys: list[str]) -> None:
        self.emit("step.completed", {"worker": worker, "outputs": output_keys})

    def step_failed(self, worker: str, error: str) -> None:
        self.emit("step.failed", {"worker": worker, "error": error})

    # ── Cancellation ──────────────────────────────────────────
    @property
    def is_cancelled(self) -> bool:
        return self.cancellation.is_set()

    def cancel(self) -> None:
        self.cancellation.set()
