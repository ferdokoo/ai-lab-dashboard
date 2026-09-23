"""
Tavily provider.

Health check probes ``POST https://api.tavily.com/search`` with a minimal
single-result query — the cheapest valid call that exercises the API key.
"""
from __future__ import annotations

import httpx

from ..config import settings
from .base import BaseProvider

_SEARCH_URL = "https://api.tavily.com/search"


class TavilyProvider(BaseProvider):
    name = "tavily"

    @property
    def api_key(self) -> str | None:
        return settings.tavily_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.post(
            _SEARCH_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"query": "ping", "max_results": 1},
        )


provider = TavilyProvider()