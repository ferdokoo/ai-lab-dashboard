"""
OpenRouter provider.

Health check probes ``GET https://openrouter.ai/api/v1/models`` — a read-only
call that lists models and validates the API key.

``request()`` reuses the OpenAI-compatible helper from ``openai.py``, pointed at
the OpenRouter endpoint.
"""
from __future__ import annotations

from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, model_entry
from .openai import chat_request

_MODELS_URL = "https://openrouter.ai/api/v1/models"
_REQUEST_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    supplies_pricing = True

    @property
    def api_key(self) -> str | None:
        return settings.openrouter_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(
            _MODELS_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    async def models(self) -> list[dict[str, Any]]:
        response = await self._list_models()
        data = response.json()
        entries: list[dict[str, Any]] = []
        for item in data.get("data", []):
            pricing = item.get("pricing") or {}
            entries.append(
                model_entry(
                    model_id=item["id"],
                    context_window=item.get("context_length"),
                    input_price_per_million=_per_million(pricing.get("prompt")),
                    output_price_per_million=_per_million(pricing.get("completion")),
                    pricing_source="api",
                )
            )
        return entries

    async def request(
        self,
        model: str,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await chat_request(
            api_key=self.api_key,
            name=self.name,
            model=model,
            prompt=prompt,
            options=options,
            base_url=_REQUEST_BASE_URL,
        )


def _per_million(value: Any) -> float | None:
    """Convert an OpenRouter per-token price string into USD per 1M tokens."""
    if value is None or value == "":
        return None
    try:
        return float(value) * 1_000_000
    except (TypeError, ValueError):
        return None


provider = OpenRouterProvider()