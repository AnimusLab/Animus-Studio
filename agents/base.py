"""
BaseWorker — all Animus Studio workers inherit from this.

Design:
  - Stateless: workers never store results on self
  - Declarative: declare requires and produces
  - Context-driven: reads/writes via ExecutionContext.artifacts
  - Auditable: every run is logged and emits events

See ARCHITECTURE_v1.md for the full contract.
"""
from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any

import structlog

from runtime.context import RuntimeContext, MissionSpec, ExecutionContext

logger = structlog.get_logger()


class AgentContext:
    """Legacy context compatibility shim."""

    def __init__(self, job_id: str, mission_id: str, brand: dict, provider: Any | None = None):
        self.job_id = job_id
        self.mission_id = mission_id
        self.brand = brand
        self.provider = provider
        self.artifacts: dict[str, Any] = {}
        self.audit_trail: list[dict] = []

    def set(self, key: str, value: Any) -> None:
        self.artifacts[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.artifacts.get(key, default)


class BaseWorker(ABC):
    """
    Abstract base for all Studio workers.
    Subclass and implement `_run()`. Declare `requires` and `produces`.
    """

    name:       str = "base"
    department: str = "core"

    # Declare capability requirements
    requires: set = set()
    # Declare what keys this worker writes to exec.artifacts
    produces: set[str] = set()

    def __init__(self) -> None:
        self._log = logger.bind(worker=self.name, department=self.department)

    # ─── Public entry point ────────────────────────────────────

    async def run(
        self,
        rt:   RuntimeContext | Any,
        spec: MissionSpec | Any = None,
        exec: ExecutionContext | Any = None,
    ) -> dict[str, Any]:
        """
        Wraps _run() with:
          - Capability validation
          - Step event emission
          - Audit logging
          - Artifact writing
        """
        task_id = str(uuid.uuid4())

        # Support both new 3-context (rt, spec, exec) and legacy (context, input_data) signatures
        if isinstance(rt, RuntimeContext) and isinstance(spec, MissionSpec) and isinstance(exec, ExecutionContext):
            mission_id = spec.mission_id
            exec.step_started(self.name)
            self._validate_requirements(rt)

            start = time.monotonic()
            try:
                result = await self._run(rt, spec, exec)
                for key, value in result.items():
                    exec.set(key, value)

                elapsed = time.monotonic() - start
                self._log.info(
                    "worker.completed",
                    task_id=task_id,
                    elapsed_ms=round(elapsed * 1000),
                    produced=list(result.keys()),
                )
                exec.step_completed(self.name, list(result.keys()))
                return result

            except Exception as exc:
                elapsed = time.monotonic() - start
                self._log.error("worker.failed", task_id=task_id, error=str(exc))
                exec.step_failed(self.name, str(exc))
                raise
        else:
            # Legacy invocation adapter
            context = rt
            input_data = spec or {}
            self._log.info("worker.started", task_id=task_id, job_id=getattr(context, "job_id", ""))
            start = time.monotonic()
            try:
                result = await self._run(context, input_data)
                elapsed = time.monotonic() - start
                self._log.info("worker.completed", task_id=task_id, elapsed_ms=round(elapsed * 1000))
                return result
            except Exception as exc:
                elapsed = time.monotonic() - start
                self._log.error("worker.failed", task_id=task_id, error=str(exc))
                raise

    # ─── Helpers for subclasses ────────────────────────────────

    def resolve(self, ctx_or_rt: Any, capability: Any) -> Any:
        """Resolve a capability from RuntimeContext or legacy AgentContext."""
        if hasattr(ctx_or_rt, "runtime") and ctx_or_rt.runtime is not None:
            return ctx_or_rt.runtime.capabilities.resolve(capability)
        elif hasattr(ctx_or_rt, "provider") and ctx_or_rt.provider is not None:
            return ctx_or_rt.provider.resolve(capability)
        else:
            from runtime.registry import runtime
            return runtime.capabilities.resolve(capability)

    async def llm_chat(
        self,
        ctx_or_rt: Any,
        messages: list[dict[str, str]],
        capability: Any | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        from runtime.capabilities import Capability
        cap      = capability or Capability.TEXT_GENERATION
        provider = self.resolve(ctx_or_rt, cap)
        return await provider.chat(messages, temperature=temperature, **kwargs)

    async def llm_json(
        self,
        ctx_or_rt: Any,
        messages: list[dict[str, str]],
        capability: Any | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> dict:
        from runtime.capabilities import Capability
        cap      = capability or Capability.TEXT_GENERATION
        provider = self.resolve(ctx_or_rt, cap)
        return await provider.chat_json(messages, temperature=temperature, **kwargs)

    # ─── Internal ──────────────────────────────────────────────

    def _validate_requirements(self, rt: RuntimeContext) -> None:
        from runtime.registry import CapabilityUnavailableError
        missing = []
        for cap in self.requires:
            try:
                rt.runtime.capabilities.resolve(cap)
            except CapabilityUnavailableError:
                missing.append(cap)
        if missing:
            raise RuntimeError(
                f"Worker '{self.name}' cannot run — missing capabilities: "
                + ", ".join(str(c) for c in missing)
            )

    @abstractmethod
    async def _run(
        self,
        rt_or_ctx: Any,
        spec_or_input: Any,
        exec_or_none: Any = None,
    ) -> dict[str, Any]:
        """Worker logic. Must return a dict of produced artifacts."""
        ...


# Backward compatibility alias
BaseAgent = BaseWorker
