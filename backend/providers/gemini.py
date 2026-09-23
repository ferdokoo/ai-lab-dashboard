"""
Google Gemini provider.

Health check probes ``GET https://generativelanguage.googleapis.com/v1beta/models``
— a read-only call that lists models and validates the API key.
"""
from __future__ import annotations

import httpx

from ..config import settings
from .base import BaseProvider

_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseProvider):
    name = "gemini"

    @property
    def api_key(self) -> str | None:
        return settings.gemini_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(_MODELS_URL, params={"key": self.api_key})


provider = GeminiProvider()