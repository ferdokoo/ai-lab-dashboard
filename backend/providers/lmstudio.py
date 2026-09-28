"""
LM Studio provider (local inference).

Probes a locally-running LM Studio server, which exposes an OpenAI-compatible
API at ``http://localhost:1234/v1`` (no API key).  Health check and model
catalog both read ``GET /v1/models``; ``request()`` posts to
``POST /v1/chat/completions`` and maps the OpenAI-compatible ``usage`` block
onto token counts.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, ProviderError, model_entry, request_result

_DEFAULT_BASE_URL = "http://localhost:1234/v1"

#: Local generation, like the cloud request runner.
_GENERATE_TIMEOUT = 120.0


class LMStudioProvider(BaseProvider):
    name = "lmstudio"
    requires_api_key = False
    resolve_pricing = False
    timeout = 10.0

    @property
    def base_url(self) -> str:
        return (settings.lmstudio_base_url or _DEFAULT_BASE_URL).rstrip("/")

    async def balance(self) -> None:
        """Local providers have no remote balance or billing to report."""
        return None

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(f"{self.base_url}/models")

    async def models(self) -> list[dict[str, Any]]:
        response = await self._list_models()
        data = response.json()
        return [model_entry(model_id=item["id"]) for item in data.get("data", [])]

    async def request(
        self,
        model: str,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        payload.update(options or {})

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=_GENERATE_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", json=payload
                )
        except httpx.TimeoutException as exc:
            raise ProviderError("Request timed out", status_code=504) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Connection failed: {exc}", status_code=502) from exc

        latency_ms = round((time.perf_counter() - started) * 1000)
        if response.status_code >= 300:
            if response.status_code == 404:
                raise ProviderError("Model not found", status_code=404)
            raise ProviderError(f"HTTP {response.status_code}", status_code=502)

        data = response.json()
        choices = data.get("choices") or []
        text = ""
        if choices and choices[0].get("message"):
            text = choices[0]["message"].get("content") or ""
        usage = data.get("usage") or {}
        return request_result(
            text=text,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            latency_ms=latency_ms,
        )


provider = LMStudioProvider()