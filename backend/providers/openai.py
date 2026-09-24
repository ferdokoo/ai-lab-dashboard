"""
OpenAI provider.

Health check probes ``GET https://api.openai.com/v1/models`` — the cheapest
read-only call that validates the API key.

``request()`` uses the official ``openai`` SDK.  The SDK is imported lazily
inside the method so a missing/optional package never prevents the server from
booting (only calling ``request``).
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, ProviderError, model_entry, request_result

_MODELS_URL = "https://api.openai.com/v1/models"

_DEFAULT_REQUEST_TIMEOUT = 120.0


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
        )


async def chat_request(
    api_key: str | None,
    name: str,
    model: str,
    prompt: str,
    options: dict[str, Any] | None = None,
    base_url: str | None = None,
    timeout: float = _DEFAULT_REQUEST_TIMEOUT,
) -> dict[str, Any]:
    """Issue an OpenAI-compatible chat completion and normalize the response.

    Shared by OpenAI and OpenRouter, which both speak the OpenAI protocol.
    """
    if not api_key:
        raise ProviderError(f"No {name} API key configured", status_code=401)

    from openai import (
        APIConnectionError,
        APIError,
        APITimeoutError,
        AsyncOpenAI,
    )

    client_kwargs: dict[str, Any] = {
        "api_key": api_key,
        "timeout": timeout,
        "max_retries": 0,
    }
    if base_url is not None:
        client_kwargs["base_url"] = base_url
    client = AsyncOpenAI(**client_kwargs)
    options = options or {}

    started = time.perf_counter()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **options,
        )
    except APITimeoutError as exc:
        raise ProviderError("Request timed out", status_code=504) from exc
    except APIConnectionError as exc:
        raise ProviderError(f"Connection failed: {exc}", status_code=502) from exc
    except APIError as exc:
        raise api_error(exc) from exc

    latency_ms = round((time.perf_counter() - started) * 1000)
    usage = response.usage
    text = ""
    if response.choices and response.choices[0].message:
        text = response.choices[0].message.content or ""

    return request_result(
        text=text,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
        latency_ms=latency_ms,
    )


def api_error(exc: Any) -> ProviderError:
    """Map an OpenAI SDK error to a :class:`ProviderError` with a clear message."""
    status = getattr(exc, "status_code", None)
    if status == 401:
        return ProviderError("Invalid API key", status_code=401)
    if status == 429:
        return ProviderError("Rate limited", status_code=429)
    if status == 404:
        return ProviderError("Model not found", status_code=404)
    message = str(exc) or exc.__class__.__name__
    return ProviderError(message, status_code=502)


provider = OpenAIProvider()