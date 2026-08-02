"""
runtime/storage.py

ArtifactStore — clean storage abstraction for Animus Studio.

Design:
  - BaseArtifactStore: abstract contract (save, load, delete, exists, cleanup)
  - LocalArtifactStore: v1 implementation (local filesystem + retention policy sweep)
  - ForgeArtifactStore: v2 target (swap in when FORGE is ready — zero refactoring required)

Retention Policy:
  - TEMP:      12h
  - RENDER:    24h
  - AUDIO:     3d
  - SCRIPT / THUMBNAIL / VIDEO / MANIFEST: forever
"""
from __future__ import annotations

import asyncio
import os
import shutil

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class ArtifactCategory(str, Enum):
    TEMP      = "temp"       # 12h retention
    RENDER    = "render"     # 24h retention
    AUDIO     = "audio"      # 3d retention
    SCRIPT    = "script"     # forever
    THUMBNAIL = "thumbnail"  # forever
    VIDEO     = "video"      # forever
    MANIFEST  = "manifest"   # forever


DEFAULT_RETENTION_POLICIES: dict[ArtifactCategory, timedelta | None] = {
    ArtifactCategory.TEMP:      timedelta(hours=12),
    ArtifactCategory.RENDER:    timedelta(hours=24),
    ArtifactCategory.AUDIO:     timedelta(days=3),
    ArtifactCategory.SCRIPT:    None,  # forever
    ArtifactCategory.THUMBNAIL: None,  # forever
    ArtifactCategory.VIDEO:     None,  # forever
    ArtifactCategory.MANIFEST:  None,  # forever
}


class BaseArtifactStore(ABC):
    @abstractmethod
    async def save(
        self,
        mission_id: str,
        name: str,
        content: bytes | str | Path,
        category: ArtifactCategory = ArtifactCategory.TEMP,
    ) -> str:
        """Save an artifact for a mission. Returns local or relative path/URI."""
        ...

    @abstractmethod
    async def load(self, mission_id: str, name: str) -> bytes:
        """Load artifact bytes."""
        ...

    @abstractmethod
    async def exists(self, mission_id: str, name: str) -> bool:
        """Check if artifact exists."""
        ...

    @abstractmethod
    async def delete(self, mission_id: str, name: str) -> bool:
        """Delete specific artifact."""
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Run lifecycle retention sweep according to policy. Returns count of purged files."""
        ...


class LocalArtifactStore(BaseArtifactStore):
    """
    v1 Storage Backend — local filesystem with retention policy cleanup.
    """

    def __init__(
        self,
        base_path: str | Path = "./storage",
        retention_policies: dict[ArtifactCategory, timedelta | None] | None = None,
    ) -> None:
        self.base_path = Path(base_path)
        self.retention_policies = retention_policies or DEFAULT_RETENTION_POLICIES
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, mission_id: str, category: ArtifactCategory, name: str) -> Path:
        target_dir = self.base_path / category.value / mission_id
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / name

    async def save(
        self,
        mission_id: str,
        name: str,
        content: bytes | str | Path,
        category: ArtifactCategory = ArtifactCategory.TEMP,
    ) -> str:
        dest_path = self._get_path(mission_id, category, name)

        if isinstance(content, Path):
            if content.resolve() != dest_path.resolve():
                shutil.copy2(content, dest_path)
        elif isinstance(content, str):
            dest_path.write_text(content, encoding="utf-8")
        elif isinstance(content, bytes):
            dest_path.write_bytes(content)

        logger.debug("storage.saved", path=str(dest_path), category=category.value)
        return str(dest_path)

    async def load(self, mission_id: str, name: str) -> bytes:
        for cat in ArtifactCategory:
            path = self.base_path / cat.value / mission_id / name
            if path.exists():
                return path.read_bytes()
        raise FileNotFoundError(f"Artifact {name} not found for mission {mission_id}")

    async def exists(self, mission_id: str, name: str) -> bool:
        for cat in ArtifactCategory:
            path = self.base_path / cat.value / mission_id / name
            if path.exists():
                return True
        return False

    async def delete(self, mission_id: str, name: str) -> bool:
        deleted = False
        for cat in ArtifactCategory:
            path = self.base_path / cat.value / mission_id / name
            if path.exists():
                path.unlink()
                deleted = True
        return deleted

    async def cleanup_expired(self) -> int:
        """
        Scans categories and purges files older than their category retention policy.
        """
        purged = 0
        now = datetime.now(timezone.utc)

        def _sweep() -> int:
            nonlocal purged
            for category, ttl in self.retention_policies.items():
                if ttl is None:
                    continue  # Keep forever

                cat_dir = self.base_path / category.value
                if not cat_dir.exists():
                    continue

                cutoff = (now - ttl).timestamp()

                for file_path in cat_dir.glob("**/*"):
                    if file_path.is_file():
                        try:
                            mtime = file_path.stat().st_mtime
                            if mtime < cutoff:
                                file_path.unlink()
                                purged += 1
                                logger.info(
                                    "storage.purged_expired",
                                    path=str(file_path),
                                    category=category.value,
                                )
                        except Exception as exc:
                            logger.warning("storage.purge_failed", path=str(file_path), error=str(exc))

            return purged

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sweep)
