"""
Tavily provider.

Health check probes ``POST https://api.tavily.com/search`` with a minimal
single-result query — the cheapest valid call that exercises the API key.

Tavily is a search tool, not an LLM: ``models()`` returns an empty catalog and
``search()`` is the request action.  Token counts are reported as ``None``
because searches consume API credits, not prompt/completion tokens.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import settings
from .base import BaseProvider, ProviderError, balance_result, request_result

_SEARCH_URL = "https://api.tavily.com/search"
_USAGE_URL = "https://api.tavily.com/usage"


class TavilyProvider(BaseProvider):
    name = "tavily"
    billing_url = "https://app.tavily.com/"

    @property
    def api_key(self) -> str | None:
        return settings.tavily_api_key

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        return await client.post(
            _SEARCH_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"query": "ping", "max_results": 1},
        )

    async def models(self) -> list[dict[str, Any]]:
        """Tavily is a search tool and exposes no model catalog."""
        return []

    async def balance(self) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError(f"No {self.name} API key configured", status_code=401)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    _USAGE_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
        except httpx.TimeoutException as exc:
            raise ProviderError("Request timed out", status_code=504) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Request failed: {exc}", status_code=502) from exc

        if response.status_code >= 300:
            if response.status_code == 401:
                raise ProviderError("Invalid API key", status_code=401)
            raise ProviderError(_response_detail(response), status_code=502)

        data = response.json() or {}
        key_usage = data.get("key") or {}
        account = data.get("account") or {}
        return balance_result(
            fields={
                "plan": account.get("plan"),
                "key_usage": key_usage.get("usage"),
                "key_limit": key_usage.get("limit"),
                "account_usage": account.get("usage"),
                "account_limit": account.get("limit"),
            },
            raw=data,
        )

    async def search(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderError(f"No {self.name} API key configured", status_code=401)

        payload: dict[str, Any] = {"query": query, **(options or {})}

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    _SEARCH_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise ProviderError("Request timed out", status_code=504) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Request failed: {exc}", status_code=502) from exc

        latency_ms = round((time.perf_counter() - started) * 1000)
        if response.status_code >= 300:
            if response.status_code == 401:
                raise ProviderError("Invalid API key", status_code=401)
            raise ProviderError(_response_detail(response), status_code=502)

        return request_result(
            text=_format_results(response.json()),
            prompt_tokens=None,
            completion_tokens=None,
            latency_ms=latency_ms,
        )


def _response_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
        detail = data.get("detail") or data.get("message") or data.get("error")
        if detail:
            return str(detail)
    except ValueError:
        pass
    return f"HTTP {response.status_code}"


def _format_results(data: dict[str, Any]) -> str:
    """Render Tavily results (answer + top results) into readable text."""
    parts: list[str] = []
    answer = data.get("answer")
    if answer:
        parts.append(str(answer))

    for index, result in enumerate(data.get("results", []), start=1):
        title = result.get("title") or ""
        url = result.get("url") or ""
        content = result.get("content") or ""
        block = f"{index}. {title}"
        if url:
            block += f" ({url})"
        if content:
            block += f"\n   {content}"
        parts.append(block)

    return "\n\n".join(parts)


provider = TavilyProvider()