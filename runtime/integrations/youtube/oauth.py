"""
runtime/integrations/youtube/oauth.py

Google OAuth2 handler for YouTube integration.
Handles authorization flow, token exchange, refresh, grant revocation, and live health verification.
"""
from __future__ import annotations

import os
import time
from typing import Any
import httpx
import structlog

logger = structlog.get_logger()

# YouTube Data API v3 OAuth Scopes
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class YouTubeOAuthHandler:
    """Google OAuth2 lifecycle implementation for YouTube."""

    def __init__(self) -> None:
        self._log = logger.bind(service="YouTubeOAuth")

    @property
    def client_id(self) -> str:
        return os.getenv("YOUTUBE_CLIENT_ID", "")

    @property
    def client_secret(self) -> str:
        return os.getenv("YOUTUBE_CLIENT_SECRET", "")

    @property
    def redirect_uri(self) -> str:
        return os.getenv(
            "YOUTUBE_REDIRECT_URI",
            "http://localhost:8000/api/v1/integrations/youtube/callback",
        )

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, brand_id: str = "default") -> str:
        """
        Generate Google OAuth authorization URL.
        Includes prompt=consent and access_type=offline to guarantee refresh_token.
        """
        if not self.is_configured():
            raise ValueError("YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET must be configured in .env")

        scope_str = "%20".join(YOUTUBE_SCOPES)
        state = f"brand={brand_id}"

        url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            "response_type=code&"
            f"scope={scope_str}&"
            "access_type=offline&"
            "prompt=consent&"
            f"state={state}"
        )
        return url

    async def exchange_code_for_tokens(self, code: str, brand_id: str = "default") -> dict[str, Any]:
        """
        Exchange authorization code for access & refresh tokens.
        Fetches channel details and saves to IntegrationManager DB.
        """
        if not self.is_configured():
            raise ValueError("YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET missing")

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(token_url, data=payload)
            resp.raise_for_status()
            token_data = resp.json()

        now = time.time()
        expires_in = token_data.get("expires_in", 3600)

        credentials = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", ""),
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": expires_in,
            "expires_at": now + expires_in,
        }

        # Fetch channel profile metadata (name, subscriber count, avatar)
        channel_info = await self.fetch_channel_info(credentials["access_token"])

        # Persist via IntegrationManager
        from runtime.integrations.manager import integration_manager
        saved = await integration_manager.save_integration(
            provider="youtube",
            brand_id=brand_id,
            credentials=credentials,
            account_name=channel_info.get("channel_name", "YouTube Channel"),
            scope=token_data.get("scope", ""),
            metadata_json=channel_info,
        )

        return {
            "status": "connected",
            "provider": "youtube",
            "brand_id": brand_id,
            "account_name": saved.account_name,
            "channel_id": channel_info.get("channel_id"),
            "expires_at": credentials["expires_at"],
        }

    async def refresh_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        """
        Refresh access token using refresh_token.
        Returns updated credentials dictionary.
        """
        refresh_token = credentials.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh_token present in credentials")

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(token_url, data=payload)
            resp.raise_for_status()
            data = resp.json()

        now = time.time()
        expires_in = data.get("expires_in", 3600)

        updated_creds = {
            **credentials,
            "access_token": data["access_token"],
            "expires_in": expires_in,
            "expires_at": now + expires_in,
        }
        # Keep existing refresh_token if Google didn't return a new one
        if "refresh_token" in data:
            updated_creds["refresh_token"] = data["refresh_token"]

        self._log.info("youtube.token_refreshed", expires_in=expires_in)
        return updated_creds

    async def fetch_channel_info(self, access_token: str) -> dict[str, Any]:
        """Call YouTube Data API v3 channels.list(mine=True) to read channel info."""
        url = "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            items = data.get("items", [])
            if not items:
                return {"channel_name": "Unknown Channel", "channel_id": "", "subscriber_count": 0, "video_count": 0}

            ch = items[0]
            snippet = ch.get("snippet", {})
            stats = ch.get("statistics", {})

            return {
                "channel_id": ch.get("id", ""),
                "channel_name": snippet.get("title", ""),
                "custom_url": snippet.get("customUrl", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "view_count": int(stats.get("viewCount", 0)),
            }
        except Exception as exc:
            self._log.warning("youtube.fetch_channel_info_failed", error=str(exc))
            return {"error": str(exc), "channel_name": "Channel (Info Fetch Failed)"}

    async def verify_channel_health(self, brand_id: str = "default") -> dict[str, Any]:
        """
        Live verification check for /verify endpoint & runtime doctor.
        Refreshes token if needed, calls channels.list, returns full health status.
        """
        from runtime.integrations.manager import integration_manager
        item = await integration_manager.get_integration("youtube", brand_id)
        if not item or not item.credentials:
            return {
                "connected": False,
                "provider": "youtube",
                "brand_id": brand_id,
                "healthy": False,
                "detail": "Not connected — add credentials or run OAuth connect flow",
            }

        try:
            valid_creds = await integration_manager.get_valid_credentials("youtube", brand_id)
            info = await self.fetch_channel_info(valid_creds["access_token"])

            # Update cached metadata
            if info and "channel_id" in info:
                await integration_manager.save_integration(
                    provider="youtube",
                    brand_id=brand_id,
                    account_name=info.get("channel_name", item.account_name),
                    metadata_json=info,
                )

            return {
                "connected": True,
                "healthy": True,
                "provider": "youtube",
                "brand_id": brand_id,
                "channel": info.get("channel_name", item.account_name),
                "channel_id": info.get("channel_id"),
                "subscriber_count": info.get("subscriber_count", 0),
                "video_count": info.get("video_count", 0),
                "expires_at": valid_creds.get("expires_at"),
            }
        except Exception as exc:
            return {
                "connected": True,
                "healthy": False,
                "provider": "youtube",
                "brand_id": brand_id,
                "channel": item.account_name,
                "error": str(exc),
                "detail": f"Token verification failed: {str(exc)}",
            }

    async def revoke_credentials(self, credentials: dict[str, Any]) -> bool:
        """Revoke grant with Google API."""
        token = credentials.get("access_token") or credentials.get("refresh_token")
        if not token:
            return True

        revoke_url = f"https://oauth2.googleapis.com/revoke?token={token}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(revoke_url)
                return resp.status_code == 200
        except Exception:
            return False


# Singleton instance
youtube_oauth = YouTubeOAuthHandler()
