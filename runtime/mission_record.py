"""
runtime/mission_record.py

MissionRecord domain model & storage manager.
Immutable (frozen=True). Acts as the single source of truth for an entire execution trace,
storing all intermediate packages, artifacts, timeline events, and publishing results for auditing & replayability.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from runtime.brand import Brand, ANIMUSLAB_BRAND
from runtime.publishing.package import PublishingPackage


@dataclass(frozen=True)
class MissionRecord:
    """
    Immutable execution record for a single Studio Mission.
    Serves as audit log, replay source, and single source of truth.
    """
    mission_id: str
    job_id: str
    spec: dict[str, Any] = field(default_factory=dict)
    brand_id: str = "AnimusLab"
    research_package: dict[str, Any] = field(default_factory=dict)
    script_package: dict[str, Any] = field(default_factory=dict)
    voice_package: dict[str, Any] = field(default_factory=dict)
    render_package: dict[str, Any] = field(default_factory=dict)
    publishing_package: dict[str, Any] = field(default_factory=dict)
    publishing_results: dict[str, Any] = field(default_factory=dict)
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    artifacts: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert MissionRecord to JSON-serializable dictionary."""
        return {
            "mission_id": self.mission_id,
            "job_id": self.job_id,
            "spec": self.spec,
            "brand_id": self.brand_id,
            "research_package": self.research_package,
            "script_package": self.script_package,
            "voice_package": self.voice_package,
            "render_package": self.render_package,
            "publishing_package": self.publishing_package,
            "publishing_results": self.publishing_results,
            "events": list(self.events),
            "artifacts": self.artifacts,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    def save(self, storage_dir: str = "./storage/mission_records") -> str:
        """Persist MissionRecord to JSON file in storage."""
        Path(storage_dir).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(storage_dir, f"{self.mission_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return file_path

    @classmethod
    def load(cls, mission_id: str, storage_dir: str = "./storage/mission_records") -> MissionRecord:
        """Load persisted MissionRecord from JSON file."""
        file_path = os.path.join(storage_dir, f"{mission_id}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"MissionRecord not found for mission_id: {mission_id}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            mission_id=data["mission_id"],
            job_id=data["job_id"],
            spec=data.get("spec", {}),
            brand_id=data.get("brand_id", "AnimusLab"),
            research_package=data.get("research_package", {}),
            script_package=data.get("script_package", {}),
            voice_package=data.get("voice_package", {}),
            render_package=data.get("render_package", {}),
            publishing_package=data.get("publishing_package", {}),
            publishing_results=data.get("publishing_results", {}),
            events=tuple(data.get("events", [])),
            artifacts=data.get("artifacts", {}),
            created_at=data.get("created_at", time.time()),
            completed_at=data.get("completed_at"),
        )
