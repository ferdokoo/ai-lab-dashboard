"""
OpenAI provider.

Health check probes ``GET https://api.openai.com/v1/models`` — the cheapest
read-only call that validates the API key.
"""
from __future__ import annotations

import httpx

from ..config import settings
from .base import BaseProvider

_MODELS_URL = "https://api.openai.com/v1/models"


class OpenAIProvider(BaseProvider):
    name = "openai"

    @property
    def api_key(self) -> str | None:
        return settings.openai_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(
            _MODELS_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )


provider = OpenAIProvider()