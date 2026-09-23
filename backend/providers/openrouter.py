"""
OpenRouter provider.

Health check probes ``GET https://openrouter.ai/api/v1/models`` — a read-only
call that lists models and validates the API key.
"""
from __future__ import annotations

import httpx

from ..config import settings
from .base import BaseProvider

_MODELS_URL = "https://openrouter.ai/api/v1/models"


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    @property
    def api_key(self) -> str | None:
        return settings.openrouter_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(
            _MODELS_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )


provider = OpenRouterProvider()