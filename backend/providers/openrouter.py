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
from .base import BaseProvider, ProviderError, balance_result, model_entry
from .openai import chat_request

_MODELS_URL = "https://openrouter.ai/api/v1/models"
_REQUEST_BASE_URL = "https://openrouter.ai/api/v1"
_CREDITS_URL = "https://openrouter.ai/api/v1/credits"


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    supplies_pricing = True
    billing_url = "https://openrouter.ai/settings/credits"

    @property
    def api_key(self) -> str | None:
        return settings.openrouter_api_key

    @property
    def management_key(self) -> str | None:
        return settings.openrouter_management_key

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

    async def balance(self) -> dict[str, Any]:
        if not self.management_key:
            raise ProviderError(
                "OpenRouter management key not configured "
                "(set OPENROUTER_MANAGEMENT_KEY in .env)",
                status_code=400,
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    _CREDITS_URL,
                    headers={"Authorization": f"Bearer {self.management_key}"},
                )
        except httpx.TimeoutException as exc:
            raise ProviderError("Request timed out", status_code=504) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Request failed: {exc}", status_code=502) from exc

        if response.status_code >= 300:
            raise ProviderError(_response_detail(response), status_code=502)

        data = (response.json() or {}).get("data") or {}
        total_credits = data.get("total_credits")
        total_usage = data.get("total_usage")
        return balance_result(
            fields={
                "total_credits": total_credits,
                "total_usage": total_usage,
                "credit_remaining": _remaining(total_credits, total_usage),
            },
            raw=data,
        )


def _per_million(value: Any) -> float | None:
    """Convert an OpenRouter per-token price string into USD per 1M tokens."""
    if value is None or value == "":
        return None
    try:
        return float(value) * 1_000_000
    except (TypeError, ValueError):
        return None


def _remaining(total_credits: Any, total_usage: Any) -> float | None:
    """Compute remaining credits, or ``None`` when either figure is missing."""
    if total_credits is None or total_usage is None:
        return None
    try:
        return round(float(total_credits) - float(total_usage), 6)
    except (TypeError, ValueError):
        return None


def _response_detail(response: httpx.Response) -> str:
    """Pull a human-readable message out of an OpenRouter error response."""
    try:
        data = response.json()
        message = (data.get("error") or {}).get("message")
        if message:
            return str(message)
    except ValueError:
        pass
    return f"HTTP {response.status_code}"


provider = OpenRouterProvider()