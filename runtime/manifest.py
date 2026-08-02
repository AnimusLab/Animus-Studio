"""
runtime/manifest.py

MissionManifest — the build artifact every mission leaves behind.

Immutable after completion. Auditable. Reproducible.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class MissionManifest:
    id:           str
    goal:         str
    brand_id:     str
    started_at:   str
    completed_at: str | None = None
    duration_s:   float      = 0.0

    workers:   list[str]       = field(default_factory=list)
    inputs:    dict[str, Any]  = field(default_factory=dict)
    outputs:   dict[str, str]  = field(default_factory=dict)   # name → path
    providers: dict[str, str]  = field(default_factory=dict)   # capability → provider/model

    cost_usd: float = 0.00
    status:   str   = "running"   # running | completed | failed
    error:    str | None = None

    # ── Lifecycle ────────────────────────────────────────────

    def complete(self, outputs: dict[str, str], providers: dict[str, str]) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.duration_s   = (
            datetime.fromisoformat(self.completed_at) -
            datetime.fromisoformat(self.started_at)
        ).total_seconds()
        self.outputs   = outputs
        self.providers = providers
        self.status    = "completed"

    def fail(self, error: str) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.status = "failed"
        self.error  = error

    # ── Serialization ─────────────────────────────────────────

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def save(self, output_dir: str) -> str:
        """Write manifest.json to the mission output directory."""
        path = Path(output_dir) / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        return str(path)

    # ── Factory ───────────────────────────────────────────────

    @classmethod
    def create(cls, mission_id: str, goal: str, brand_id: str, workers: list[str]) -> "MissionManifest":
        return cls(
            id=mission_id,
            goal=goal,
            brand_id=brand_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            workers=workers,
        )
