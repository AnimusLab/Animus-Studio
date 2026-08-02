"""
runtime/integrations/base_connection.py

BaseConnection abstraction — returned by integration_manager.get_connection(provider, brand_id).
Encapsulates valid, auto-refreshing credentials and provider-native API actions.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class BaseConnection(ABC):
    """
    Abstract connection returned by IntegrationManager.get_connection().
    Self-refreshes credentials and provides high-level API methods.
    """

    def __init__(self, provider: str, brand_id: str, credentials: dict[str, Any], account_name: str = ""):
        self.provider = provider
        self.brand_id = brand_id
        self.credentials = credentials
        self.account_name = account_name

    @property
    def access_token(self) -> str:
        return self.credentials.get("access_token", "")

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check connection health with provider API."""
        ...
