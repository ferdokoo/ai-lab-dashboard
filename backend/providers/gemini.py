"""
Google Gemini provider.

Health check probes ``GET https://generativelanguage.googleapis.com/v1beta/models``
— a read-only call that lists models and validates the API key.

``request()`` uses the official ``google-genai`` SDK, imported lazily.  Unlike
the REST clients, ``options`` map onto a ``GenerateContentConfig`` rather than
arbitrary keyword arguments.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, ProviderError, model_entry, request_result

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

    async def request(
        self,
        model: str,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError(f"No {self.name} API key configured", status_code=401)

        from google import genai
        from google.genai import types
        from google.genai import errors as genai_errors

        client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(**(options or {}))

        started = time.perf_counter()
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
        except genai_errors.APIError as exc:
            raise _gemini_api_error(exc) from exc

        latency_ms = round((time.perf_counter() - started) * 1000)
        usage = response.usage_metadata
        text = ""
        try:
            text = response.text or ""
        except Exception:
            text = ""

        return request_result(
            text=text,
            prompt_tokens=usage.prompt_token_count if usage else None,
            completion_tokens=usage.candidates_token_count if usage else None,
            latency_ms=latency_ms,
        )


def _gemini_api_error(exc: Any) -> ProviderError:
    code = getattr(exc, "code", None)
    if code == 401:
        return ProviderError("Invalid API key", status_code=401)
    if code == 429:
        return ProviderError("Rate limited", status_code=429)
    if code == 404:
        return ProviderError("Model not found", status_code=404)
    message = str(exc) or exc.__class__.__name__
    return ProviderError(message, status_code=502)


provider = GeminiProvider()