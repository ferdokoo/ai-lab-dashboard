"""
Anthropic provider.

Health check probes ``GET https://api.anthropic.com/v1/models`` — a read-only
call that lists models and validates the API key.
"""
from __future__ import annotations

import httpx

from ..config import settings
from .base import BaseProvider

_MODELS_URL = "https://api.anthropic.com/v1/models"


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    @property
    def api_key(self) -> str | None:
        return settings.anthropic_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(
            _MODELS_URL,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )


provider = AnthropicProvider()