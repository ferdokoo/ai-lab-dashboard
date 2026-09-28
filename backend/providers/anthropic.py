"""
Anthropic provider.

Health check probes ``GET https://api.anthropic.com/v1/models`` — a read-only
call that lists models and validates the API key.

``request()`` uses the official ``anthropic`` SDK, imported lazily so the server
boots even if the package is absent.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, ProviderError, model_entry, request_result

_MODELS_URL = "https://api.anthropic.com/v1/models"

_DEFAULT_MAX_TOKENS = 1024
_DEFAULT_REQUEST_TIMEOUT = 120.0


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    billing_url = "https://console.anthropic.com/settings/billing"

    @property
    def api_key(self) -> str | None:
        return settings.anthropic_api_key

    async def balance(self) -> None:
        """Anthropic exposes no account-balance endpoint via its API."""
        return None

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(
            _MODELS_URL,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
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
        if not self.api_key:
            raise ProviderError(f"No {self.name} API key configured", status_code=401)

        from anthropic import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            AsyncAnthropic,
        )

        client = AsyncAnthropic(
            api_key=self.api_key,
            timeout=_DEFAULT_REQUEST_TIMEOUT,
            max_retries=0,
        )
        options = dict(options or {})
        max_tokens = options.pop("max_tokens", _DEFAULT_MAX_TOKENS)

        started = time.perf_counter()
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                **options,
            )
        except APITimeoutError as exc:
            raise ProviderError("Request timed out", status_code=504) from exc
        except APIConnectionError as exc:
            raise ProviderError(f"Connection failed: {exc}", status_code=502) from exc
        except APIStatusError as exc:
            raise _anthropic_api_error(exc) from exc

        latency_ms = round((time.perf_counter() - started) * 1000)
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        usage = response.usage
        return request_result(
            text=text,
            prompt_tokens=usage.input_tokens if usage else None,
            completion_tokens=usage.output_tokens if usage else None,
            latency_ms=latency_ms,
        )


def _anthropic_api_error(exc: Any) -> ProviderError:
    status = getattr(exc, "status_code", None)
    if status == 401:
        return ProviderError("Invalid API key", status_code=401)
    if status == 429:
        return ProviderError("Rate limited", status_code=429)
    if status == 404:
        return ProviderError("Model not found", status_code=404)
    message = str(exc) or exc.__class__.__name__
    return ProviderError(message, status_code=502)


provider = AnthropicProvider()