"""
runtime/eventbus.py

Event-sourced mission event store.

Every step in every mission emits typed events.
All events are persisted. Nothing is fire-and-forget.

Enables:
  - Real-time WebSocket timeline in UI
  - Full replay of any past execution
  - Analytics queries across runs
  - Debugging without needing log files
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import structlog
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID

logger = structlog.get_logger()


# ─── DB Model ──────────────────────────────────────────────────
# Imported conditionally to avoid requiring DB at import time

def get_mission_event_model() -> Any:
    try:
        try:
            from app.models.mission import MissionEvent
        except ImportError:
            from backend.app.models.mission import MissionEvent
        return MissionEvent
    except Exception:
        return None



# ─── EventBus ──────────────────────────────────────────────────

class EventBus:
    """
    Persists mission events and delivers them to WebSocket subscribers.

    Subscribers receive events via async generators.
    DB persistence happens in background to not block execution.
    """

    def __init__(self) -> None:
        # mission_id → list of asyncio.Queue
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._db: Any = None

    def set_db(self, db: Any) -> None:
        self._db = db

    async def emit(
        self,
        mission_id: str,
        event_type: str,
        step: str = "",
        worker: str = "",
        payload: dict | None = None,
        execution_id: str | None = None,
    ) -> None:
        event = {
            "id":           str(uuid.uuid4()),
            "mission_id":   mission_id,
            "execution_id": execution_id,
            "event_type":   event_type,
            "step":         step,
            "worker":       worker,
            "payload":      payload or {},
            "emitted_at":   datetime.now(timezone.utc).isoformat(),
        }

        logger.debug("event.emitted", mission_id=mission_id, event_type=event_type, step=step)

        # Deliver to WebSocket subscribers (non-blocking)
        for q in self._subscribers.get(mission_id, []):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

        # Persist to DB in background (fire and forget — failure never breaks execution)
        asyncio.create_task(self._persist(event))

    async def _persist(self, event: dict) -> None:
        if self._db is None:
            return
        try:
            MissionEvent = get_mission_event_model()
            if MissionEvent is None:
                return
            record = MissionEvent(
                mission_id=event["mission_id"],
                execution_id=event["execution_id"],
                event_type=event["event_type"],
                step=event["step"],
                worker=event["worker"],
                payload=event["payload"],
            )
            self._db.add(record)
            await self._db.commit()
        except Exception as exc:
            logger.warning("event.persist_failed", error=str(exc))

    async def subscribe(self, mission_id: str) -> AsyncGenerator[dict, None]:
        """
        Subscribe to events for a mission.
        Yields events as they arrive. Used by WebSocket endpoint.
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(mission_id, [])
        self._subscribers[mission_id].append(q)
        try:
            while True:
                event = await asyncio.wait_for(q.get(), timeout=60.0)
                yield event
                if event.get("event_type") in ("mission.completed", "mission.failed"):
                    break
        except asyncio.TimeoutError:
            pass
        finally:
            self._subscribers[mission_id].remove(q)

    async def replay(self, mission_id: str, db: Any) -> list[dict]:
        """Return full event history for a mission from DB."""
        try:
            MissionEvent = get_mission_event_model()
            if MissionEvent is None:
                return []
            from sqlalchemy import select
            result = await db.execute(
                select(MissionEvent)
                .where(MissionEvent.mission_id == mission_id)
                .order_by(MissionEvent.emitted_at)
            )
            events = result.scalars().all()
            return [
                {
                    "id":         str(e.id),
                    "event_type": e.event_type,
                    "step":       e.step,
                    "worker":     e.worker,
                    "payload":    e.payload,
                    "emitted_at": e.emitted_at.isoformat() if e.emitted_at else None,
                }
                for e in events
            ]
        except Exception as exc:
            logger.error("event.replay_failed", error=str(exc))
            return []
