"""
Google Gemini provider.

Health check probes ``GET https://generativelanguage.googleapis.com/v1beta/models``
— a read-only call that lists models and validates the API key.
"""
from __future__ import annotations

from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, model_entry

_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseProvider):
    name = "gemini"

    @property
    def api_key(self) -> str | None:
        return settings.gemini_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(_MODELS_URL, params={"key": self.api_key})

    async def models(self) -> list[dict[str, Any]]:
        response = await self._list_models()
        data = response.json()
        return [
            model_entry(model_id=item["name"].removeprefix("models/"),
                        context_window=item.get("inputTokenLimit"))
            for item in data.get("models", [])
        ]


provider = GeminiProvider()