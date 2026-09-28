"""
Ollama provider (local inference).

Probes a locally-running Ollama server at ``http://localhost:11434`` (no API
key).  Health check and model catalog both read ``GET /api/tags`` — the
cheapest read-only call that lists pulled models.  ``request()`` posts to
``POST /api/generate`` with ``stream: false`` and maps the response's
``prompt_eval_count`` / ``eval_count`` onto token counts.
"""
from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import httpx

from ..config import settings
from .base import BaseProvider, ProviderError, model_entry, request_result

_DEFAULT_BASE_URL = "http://localhost:11434"

#: Local models can take a while to load and generate; be generous.
_GENERATE_TIMEOUT = 120.0


class OllamaProvider(BaseProvider):
    name = "ollama"
    requires_api_key = False
    resolve_pricing = False
    timeout = 10.0

    @property
    def base_url(self) -> str:
        return (settings.ollama_base_url or _DEFAULT_BASE_URL).rstrip("/")

    async def balance(self) -> None:
        """Local providers have no remote balance or billing to report."""
        return None

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.get(f"{self.base_url}/api/tags")

    async def models(self) -> list[dict[str, Any]]:
        response = await self._list_models()
        data = response.json()
        return [model_entry(model_id=item["name"]) for item in data.get("models", [])]

    async def request(
        self,
        model: str,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        payload.update(options or {})

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=_GENERATE_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate", json=payload
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
        return request_result(
            text=data.get("response", ""),
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            latency_ms=latency_ms,
        )

    async def stream(
        self,
        model: str,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
        payload.update(options or {})

        try:
            async with httpx.AsyncClient(timeout=_GENERATE_TIMEOUT) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/generate", json=payload
                ) as response:
                    if response.status_code >= 300:
                        if response.status_code == 404:
                            raise ProviderError("Model not found", status_code=404)
                        raise ProviderError(
                            f"HTTP {response.status_code}", status_code=502
                        )
                    prompt_tokens: int | None = None
                    completion_tokens: int | None = None
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if chunk.get("done"):
                            prompt_tokens = chunk.get("prompt_eval_count")
                            completion_tokens = chunk.get("eval_count")
                            break
                        content = chunk.get("response") or ""
                        if content:
                            yield {"type": "delta", "content": content}
        except httpx.TimeoutException as exc:
            raise ProviderError("Request timed out", status_code=504) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Connection failed: {exc}", status_code=502) from exc

        yield {
            "type": "done",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }


provider = OllamaProvider()