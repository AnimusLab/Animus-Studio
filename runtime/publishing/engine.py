"""
runtime/publishing/engine.py

PublishingEngine — Central platform orchestrator.
Decoupled from specific social platform APIs.
Resolves publishers dynamically via registry without platform 'if' statements.
"""
from __future__ import annotations

from typing import Any
import structlog

from runtime.integrations.manager import integration_manager
from runtime.publishing.package import PublishingPackage
from runtime.publishing.result import PublishingResult
from runtime.publishing.publishers.base import BasePublisher
from runtime.publishing.publishers.youtube import YouTubePublisher

logger = structlog.get_logger()


class PublisherRegistry:
    """Registry mapping platform names to BasePublisher instances."""

    def __init__(self) -> None:
        self._publishers: dict[str, BasePublisher] = {
            "youtube": YouTubePublisher(),
        }

    def register(self, publisher: BasePublisher) -> None:
        self._publishers[publisher.provider.lower()] = publisher

    def resolve(self, platform: str) -> BasePublisher:
        key = platform.lower()
        if key not in self._publishers:
            raise ValueError(f"No publisher plugin registered for platform: '{platform}'")
        return self._publishers[key]


class PublishingEngine:
    """
    Central engine orchestrating multi-platform publishing.
    Decoupled from specific API implementations.
    """

    def __init__(self, registry: PublisherRegistry | None = None) -> None:
        self.registry = registry or PublisherRegistry()
        self._log = logger.bind(component="PublishingEngine")

    async def publish(
        self,
        package: PublishingPackage,
        platform: str = "youtube",
        brand_id: str = "default",
    ) -> PublishingResult:
        """
        Orchestrates publishing:
          1. Resolves publisher plugin dynamically (no platform 'if' checks).
          2. Obtains valid, auto-refreshing connection from IntegrationManager.
          3. Executes publisher.publish(package, connection).
          4. Returns PublishingResult.
        """
        self._log.info("engine.publish.starting", platform=platform, brand_id=brand_id, title=package.title)

        # 1. Resolve publisher plugin dynamically from registry
        publisher = self.registry.resolve(platform)

        # 2. Fetch active, auto-refreshing connection
        connection = await integration_manager.get_connection(platform, brand_id=brand_id)

        # 3. Delegate execution to publisher plugin
        result = await publisher.publish(package=package, connection=connection, brand_id=brand_id)

        self._log.info(
            "engine.publish.completed",
            platform=platform,
            brand_id=brand_id,
            status=result.status,
            url=result.url,
        )
        return result


# Global singleton instance
publishing_engine = PublishingEngine()
