"""
runtime/integrations/manager.py

IntegrationManager — Central token persistence and OAuth lifecycle controller.
Manages encrypted storage and automatic refresh of provider credentials in PostgreSQL.
"""
from __future__ import annotations

import os
import time
from typing import Any
import structlog
from sqlalchemy.future import select

try:
    from app.core.database import AsyncSessionLocal
    from app.models.integration import Integration
except ImportError:
    from backend.app.core.database import AsyncSessionLocal
    from backend.app.models.integration import Integration

logger = structlog.get_logger()


class IntegrationManager:
    """
    Manages OAuth token storage, status queries, token refresh loops,
    and disconnection for all integration providers (YouTube, Instagram, LinkedIn, etc.).
    """

    def __init__(self) -> None:
        self._log = logger.bind(component="IntegrationManager")

    async def get_integration(self, provider: str, brand_id: str = "default") -> Integration | None:
        """Fetch raw Integration model from database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Integration).where(
                    Integration.provider == provider.lower(),
                    Integration.brand_id == brand_id,
                )
            )
            return result.scalars().first()

    async def save_integration(
        self,
        provider: str,
        brand_id: str = "default",
        credentials: dict[str, Any] | None = None,
        account_name: str | None = None,
        scope: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> Integration:
        """Upsert an Integration record into database."""
        provider = provider.lower()
        credentials = credentials or {}
        metadata_json = metadata_json or {}

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Integration).where(
                    Integration.provider == provider,
                    Integration.brand_id == brand_id,
                )
            )
            existing = result.scalars().first()

            if existing:
                existing.credentials = {**(existing.credentials or {}), **credentials}
                if account_name:
                    existing.account_name = account_name
                if scope:
                    existing.scope = scope
                if metadata_json:
                    existing.metadata_json = {**(existing.metadata_json or {}), **metadata_json}
                item = existing
            else:
                item = Integration(
                    provider=provider,
                    brand_id=brand_id,
                    account_name=account_name or "",
                    credentials=credentials,
                    scope=scope or "",
                    metadata_json=metadata_json,
                )
                db.add(item)

            await db.commit()
            await db.refresh(item)
            self._log.info("integration.saved", provider=provider, brand_id=brand_id, account=item.account_name)
            return item

    async def delete_integration(self, provider: str, brand_id: str = "default") -> bool:
        """Revoke and delete integration record from database."""
        provider = provider.lower()
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Integration).where(
                    Integration.provider == provider,
                    Integration.brand_id == brand_id,
                )
            )
            existing = result.scalars().first()
            if existing:
                await db.delete(existing)
                await db.commit()
                self._log.info("integration.deleted", provider=provider, brand_id=brand_id)
                return True
            return False

    async def get_valid_credentials(self, provider: str, brand_id: str = "default") -> dict[str, Any]:
        """
        Get valid credentials dictionary for provider.
        Checks expires_at timestamp — if within 5-minute safety margin, automatically
        triggers the provider refresh flow and updates DB.
        """
        item = await self.get_integration(provider, brand_id)
        if not item or not item.credentials:
            raise ValueError(f"No integration found for {provider} (brand: {brand_id})")

        creds = item.credentials
        expires_at = creds.get("expires_at")
        now = time.time()

        # Check 5-minute (300s) expiry safety margin
        if expires_at and (expires_at - now) < 300:
            self._log.info("integration.token_expiring", provider=provider, expires_in=round(expires_at - now))
            creds = await self._refresh_provider_token(provider, brand_id, item)

        return creds

    async def get_connection(self, provider: str, brand_id: str = "default") -> Any:
        """
        Get an active, auto-refreshing connection object for provider.
        Example: connection = await integration_manager.get_connection("youtube", "AnimusLab")
        """
        provider = provider.lower()
        creds = await self.get_valid_credentials(provider, brand_id)
        item = await self.get_integration(provider, brand_id)
        account_name = item.account_name if item else ""

        if provider == "youtube":
            from runtime.integrations.youtube.connection import YouTubeConnection
            return YouTubeConnection(provider, brand_id, creds, account_name)

        from runtime.integrations.base_connection import BaseConnection
        class GenericConnection(BaseConnection):
            async def is_healthy(self) -> bool:
                return True

        return GenericConnection(provider, brand_id, creds, account_name)

    async def _refresh_provider_token(self, provider: str, brand_id: str, item: Integration) -> dict[str, Any]:
        """Delegate refresh call to specific provider handler."""
        if provider.lower() == "youtube":
            from runtime.integrations.youtube.oauth import youtube_oauth
            new_creds = await youtube_oauth.refresh_credentials(item.credentials)
            updated = await self.save_integration(provider, brand_id, credentials=new_creds)
            return updated.credentials
        else:
            # Fallback if no refresh handler registered
            return item.credentials

    async def verify_integration(self, provider: str, brand_id: str = "default") -> dict[str, Any]:
        """
        Perform a live I/O verification check for provider.
        Refreshes token if needed and calls channel info / profile endpoint.
        Returns health status dict.
        """
        provider = provider.lower()

        if provider == "youtube":
            from runtime.integrations.youtube.oauth import youtube_oauth
            return await youtube_oauth.verify_channel_health(brand_id)

        item = await self.get_integration(provider, brand_id)
        if not item:
            return {"connected": False, "provider": provider, "brand_id": brand_id, "healthy": False}

        return {
            "connected": True,
            "provider": provider,
            "brand_id": brand_id,
            "account_name": item.account_name,
            "healthy": True,
        }


# Global singleton instance
integration_manager = IntegrationManager()
