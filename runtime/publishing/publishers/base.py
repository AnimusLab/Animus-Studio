"""
runtime/publishing/publishers/base.py

BasePublisher abstract contract.
All platform publisher plugins (YouTubePublisher, InstagramPublisher, etc.) inherit from this.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from runtime.integrations.base_connection import BaseConnection
from runtime.publishing.capabilities import PlatformCapabilities
from runtime.publishing.package import PublishingPackage
from runtime.publishing.result import PublishingResult


class BasePublisher(ABC):
    """
    Abstract platform publisher plugin.
    Takes a canonical PublishingPackage and an active BaseConnection,
    renders the metadata according to its PlatformCapabilities, and executes the upload.
    """
    provider: str = "base"
    capabilities: PlatformCapabilities

    @abstractmethod
    async def publish(
        self,
        package: PublishingPackage,
        connection: BaseConnection,
        brand_id: str = "default",
    ) -> PublishingResult:
        """Render package according to platform capabilities and upload."""
        ...
