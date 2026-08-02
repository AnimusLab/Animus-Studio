"""
runtime/credentials.py

CredentialManager — one abstraction for all Studio credentials.

Workers never call os.getenv() for secrets.
They call: runtime.credentials.get("youtube")

v1 backends:
  API keys   → .env (read at startup, immutable)
  OAuth      → Postgres (encrypted, refreshable)

v2: Vault / AWS Secrets Manager — same interface.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class APIKeyCredential:
    key:     str
    service: str

    @property
    def is_valid(self) -> bool:
        return bool(self.key)


@dataclass
class OAuthCredential:
    service:       str
    access_token:  str
    refresh_token: str
    expires_at:    datetime
    scopes:        list[str] = field(default_factory=list)
    extra:         dict      = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        return bool(self.access_token) and not self.is_expired


Credential = APIKeyCredential | OAuthCredential


# ── Service → env var mapping (for API keys in .env) ──────────
_ENV_KEY_MAP: dict[str, str] = {
    "openai":      "OPENAI_API_KEY",
    "anthropic":   "ANTHROPIC_API_KEY",
    "groq":        "GROQ_API_KEY",
    "openrouter":  "OPENROUTER_API_KEY",
    "google":      "GOOGLE_API_KEY",
    "elevenlabs":  "ELEVENLABS_API_KEY",
    "tavily":      "TAVILY_API_KEY",
    "brave":       "BRAVE_API_KEY",
    "serper":      "SERPER_API_KEY",
    "firecrawl":   "FIRECRAWL_API_KEY",
    "github":      "GITHUB_TOKEN",
    "twitter":     "TWITTER_API_KEY",
}


class CredentialManager:
    """
    v1: reads API keys from .env, OAuth tokens from DB.
    Interface is stable — swap backend in v2 without changing callers.
    """

    def __init__(self) -> None:
        self._cache:   dict[str, Credential] = {}
        self._db:      Any = None   # injected when DB session is available

    def set_db(self, db: Any) -> None:
        self._db = db

    # ── Get ───────────────────────────────────────────────────

    def get(self, service: str) -> Credential | None:
        """
        Synchronous get. Returns cached credential.
        For OAuth tokens, call async get_oauth() to ensure refresh.
        """
        if service in self._cache:
            return self._cache[service]

        # Try .env API key
        env_var = _ENV_KEY_MAP.get(service.lower())
        if env_var:
            key = os.getenv(env_var, "")
            if key:
                cred = APIKeyCredential(key=key, service=service)
                self._cache[service] = cred
                return cred

        return None

    async def get_oauth(self, service: str) -> OAuthCredential | None:
        """
        Async get for OAuth credentials. Refreshes if expired.
        Reads from DB — requires set_db() to have been called.
        """
        if service in self._cache:
            cred = self._cache[service]
            if isinstance(cred, OAuthCredential):
                if cred.is_expired:
                    return await self.refresh(service)
                return cred

        # TODO: read from DB when integration table is wired
        return None

    async def store(self, service: str, cred: Credential) -> None:
        """Persist an OAuth credential to the DB."""
        self._cache[service] = cred
        # TODO: encrypt and write to integrations table

    async def refresh(self, service: str) -> OAuthCredential | None:
        """Refresh an expired OAuth token."""
        cred = self._cache.get(service)
        if not isinstance(cred, OAuthCredential):
            return None
        # Service-specific refresh logic goes here
        # For now: return as-is and let the caller handle expiry
        return cred

    def is_configured(self, service: str) -> bool:
        """Quick check — does this service have any credential?"""
        return self.get(service) is not None

    def configured_services(self) -> list[str]:
        """List all services that have credentials."""
        services = []
        for service, env_var in _ENV_KEY_MAP.items():
            if os.getenv(env_var):
                services.append(service)
        return services
