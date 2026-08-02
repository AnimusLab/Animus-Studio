"""
Publisher Agent — Department: Publishing

Capabilities required:
  - PUBLISH

Delegates publishing execution directly to PublishingEngine and MetadataGenerator.
Zero platform-specific API calls in agent logic.
"""
from __future__ import annotations
import os
from typing import Any

from agents.base import BaseAgent
from runtime.capabilities import Capability
from runtime.publishing.engine import publishing_engine
from runtime.services.metadata import metadata_generator
from runtime.brand import brand_registry


class PublisherAgent(BaseAgent):
    name = "publisher"
    department = "publishing"
    requires = {Capability.PUBLISH}
    produces = {"publish_results"}

    async def _run(self, rt_or_ctx: Any, spec_or_input: Any, exec_or_none: Any = None) -> dict[str, Any]:
        if exec_or_none is not None:
            exec_ctx = exec_or_none
            video_path = exec_ctx.get("video_path")
            script = exec_ctx.get("script", {})
            brief = exec_ctx.get("research_brief", {})
            brand_id = exec_ctx.get("brand", {}).get("id", "AnimusLab")
            channels = getattr(spec_or_input, "channels", [{"platform": "youtube"}])
        else:
            context = rt_or_ctx
            input_data = spec_or_input or {}
            video_path = context.get("video_path", input_data.get("video_path"))
            script = context.get("script", {})
            brief = context.get("research_brief", {})
            brand_id = context.get("brand", {}).get("id", "AnimusLab")
            channels = input_data.get("channels", [{"platform": "youtube"}])

        if not video_path or not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")

        # Resolve Brand execution context
        brand = brand_registry.get(brand_id)

        # Synthesize canonical PublishingPackage
        package = metadata_generator.create_package(
            script=script,
            brief=brief,
            brand=brand,
            video_path=video_path,
        )

        results = {}
        for channel in channels:
            platform = channel.get("platform") if isinstance(channel, dict) else str(channel)
            self._log.info("publisher.dispatching_engine", platform=platform, brand=brand_id)

            try:
                # Delegate execution to PublishingEngine
                result = await publishing_engine.publish(
                    package=package,
                    platform=platform,
                    brand_id=brand.id,
                )
                results[platform] = {
                    "status": result.status,
                    "platform": result.provider,
                    "video_id": result.video_id,
                    "url": result.url,
                    "studio_url": result.studio_url,
                    "visibility": result.visibility,
                    "error": result.error,
                }
            except Exception as exc:
                self._log.warning("publisher.engine_failed", platform=platform, error=str(exc))
                results[platform] = {"status": "failed", "error": str(exc)}

        if hasattr(rt_or_ctx, "set"):
            rt_or_ctx.set("publish_results", results)

        return {"publish_results": results, "published_to": list(results.keys())}
