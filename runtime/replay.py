"""
runtime/replay.py

Granular Mission Replay Engine for V2.
Allows resuming/replaying a mission starting from any execution stage without re-running upstream steps:
  - 'script'    → Re-uses research_package, re-runs script, voice, editor, thumbnail, publishing
  - 'voice'     → Re-uses script_package, re-runs voice, editor, thumbnail, publishing
  - 'editor'    → Re-uses voice_package, re-runs editor, thumbnail, publishing
  - 'thumbnail' → Re-runs thumbnail generation only
  - 'publish'   → Re-runs PublishingEngine upload only
"""
from __future__ import annotations

import os
import time
from typing import Any
import structlog

from runtime.brand import brand_registry
from runtime.mission_record import MissionRecord
from runtime.publishing.package import PublishingPackage
from runtime.publishing.engine import publishing_engine
from runtime.services.metadata import metadata_generator
from agents.script.agent import ScriptAgent
from agents.voice.agent import VoiceAgent
from agents.editor.agent import EditorAgent
from agents.thumbnail.agent import ThumbnailAgent
from agents.publisher.agent import PublisherAgent
from agents.base import AgentContext
from runtime.registry import runtime as registry

logger = structlog.get_logger()

VALID_STAGES = {"script", "voice", "editor", "thumbnail", "publish"}


async def replay_mission(
    mission_id: str,
    from_stage: str = "script",
    storage_dir: str = "./storage/mission_records",
) -> MissionRecord:
    """Replays a persisted mission from a specific stage."""
    from_stage = from_stage.lower()
    if from_stage not in VALID_STAGES:
        raise ValueError(f"Invalid replay stage '{from_stage}'. Must be one of: {sorted(VALID_STAGES)}")

    # Load existing MissionRecord
    record = MissionRecord.load(mission_id, storage_dir=storage_dir)
    brand = brand_registry.get(record.brand_id)

    log = logger.bind(component="ReplayEngine", mission_id=mission_id, from_stage=from_stage)
    log.info("replay.starting", brand=brand.id)

    events_list = list(record.events)
    def log_event(event_type: str, detail: str = ""):
        evt = {"event_type": event_type, "timestamp": time.time(), "detail": detail}
        events_list.append(evt)
        print(f"  🔁 [{event_type:<22}] {detail}")

    log_event("replay.started", f"Replaying mission from stage: '{from_stage}'")

    ctx = AgentContext(
        job_id=record.job_id,
        mission_id=record.mission_id,
        brand=brand.__dict__,
        provider=registry,
    )

    # Pre-populate context with existing artifacts
    ctx.set("research_brief", record.research_package)
    ctx.set("script", record.script_package)

    artifacts = dict(record.artifacts)
    if "audio_path" in artifacts:
        ctx.set("audio_path", artifacts["audio_path"])
    if "video_path" in artifacts:
        ctx.set("video_path", artifacts["video_path"])

    script_res = record.script_package
    voice_res = record.voice_package
    render_res = record.render_package
    thumbnail_res = record.artifacts.get("thumbnail_path")
    publish_res = record.publishing_results

    # ── Stage: Script ─────────────────────────────────────────────
    if from_stage in ("script",):
        log_event("script.replay_started")
        script_agent = ScriptAgent()
        script_res = await script_agent.run(ctx, {"mission": record.spec})
        ctx.set("script", script_res)
        log_event("script.replay_completed", f"Title: {script_res.get('title')}")

    # ── Stage: Voice ──────────────────────────────────────────────
    if from_stage in ("script", "voice"):
        log_event("voice.replay_started")
        voice_agent = VoiceAgent()
        voice_res = await voice_agent.run(ctx, {})
        artifacts["audio_path"] = voice_res.get("audio_path", "")
        log_event("voice.replay_completed", f"Audio: {artifacts['audio_path']}")

    # ── Stage: Editor ─────────────────────────────────────────────
    if from_stage in ("script", "voice", "editor"):
        log_event("editor.replay_started")
        editor_agent = EditorAgent()
        render_res = await editor_agent.run(ctx, {})
        artifacts["video_path"] = render_res.get("video_path", "")
        log_event("editor.replay_completed", f"Video: {artifacts['video_path']}")

    # ── Stage: Thumbnail ──────────────────────────────────────────
    if from_stage in ("script", "voice", "editor", "thumbnail"):
        log_event("thumbnail.replay_started")
        thumb_agent = ThumbnailAgent()
        thumb_out = await thumb_agent.run(ctx, {"script": script_res, "brand": brand.__dict__})
        artifacts["thumbnail_path"] = thumb_out.get("thumbnail_path", "")
        log_event("thumbnail.replay_completed", f"Thumbnail: {artifacts['thumbnail_path']}")

    # ── Stage: Publish ────────────────────────────────────────────
    if from_stage in ("script", "voice", "editor", "thumbnail", "publish"):
        log_event("publish.replay_started")
        pkg = metadata_generator.create_package(
            script=script_res,
            brief=record.research_package,
            brand=brand,
            video_path=artifacts.get("video_path", ""),
            thumbnail_path=artifacts.get("thumbnail_path"),
        )
        publisher_agent = PublisherAgent()
        pub_out = await publisher_agent.run(ctx, {"channels": [{"platform": "youtube"}]})
        publish_res = pub_out.get("publish_results", {})
        log_event("publish.replay_completed", f"Results: {publish_res}")

    log_event("replay.completed", "Replay execution trace finished")

    updated_record = MissionRecord(
        mission_id=record.mission_id,
        job_id=record.job_id,
        spec=record.spec,
        brand_id=record.brand_id,
        research_package=record.research_package,
        script_package=script_res,
        voice_package=voice_res,
        render_package=render_res,
        publishing_package={
            "title": script_res.get("title", ""),
            "description": script_res.get("description", "")[:100],
            "tags": list(script_res.get("tags", [])),
        },
        publishing_results=publish_res,
        events=tuple(events_list),
        artifacts=artifacts,
        created_at=record.created_at,
        completed_at=time.time(),
    )

    updated_record.save(storage_dir=storage_dir)
    return updated_record
