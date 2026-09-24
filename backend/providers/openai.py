"""
OpenAI provider.

Health check probes ``GET https://api.openai.com/v1/models`` — the cheapest
read-only call that validates the API key.
"""
from __future__ import annotations

from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, model_entry

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

    async def models(self) -> list[dict[str, Any]]:
        response = await self._list_models()
        data = response.json()
        return [model_entry(model_id=item["id"]) for item in data.get("data", [])]


provider = OpenAIProvider()