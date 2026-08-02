"""Base Search Provider"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from runtime.capabilities import Capability



@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str


class BaseSearchProvider(ABC):
    name: str = "base_search"
    priority: int = 100
    is_cloud: bool = False
    capabilities = {Capability.WEB_SEARCH}
    model: str = ""


    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]: ...
