"""
Request-runner routes.

* ``POST /api/{provider}/request`` — send a prompt to a cloud LLM provider and
  return text + token usage + latency.  Gated to LLM providers; Tavily has its
  own search route.
* ``POST /api/{provider}/search`` — run a search (Tavily).  The query travels as
  its own field and token metrics are reported honestly as ``None``.

Every call — successful or failed — is written to the SQLite request log with
counts and latency only (never prompt/response bodies).
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import cost, requestlog
from ..providers import PROVIDERS
from ..providers.base import ProviderError

router = APIRouter(prefix="/api", tags=["request"])

#: Providers whose action is a Tavily-style search rather than an LLM completion.
_SEARCH_ONLY = {"tavily"}


class RequestBody(BaseModel):
    model: str
    prompt: str
    options: dict[str, Any] = Field(default_factory=dict)


class SearchBody(BaseModel):
    query: str
    options: dict[str, Any] = Field(default_factory=dict)


@router.post("/{provider}/request")
async def provider_request(provider: str, body: RequestBody) -> dict[str, Any]:
    """Send a completion request to a cloud LLM provider."""
    name = _resolve_provider(provider)

    if name in _SEARCH_ONLY:
        raise HTTPException(
            status_code=400,
            detail=f"{name.title()} is a search provider; use POST /api/{name}/search",
        )

    model = body.model.strip()
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    started = time.perf_counter()
    try:
        result = await PROVIDERS[name].request(model, body.prompt, body.options)
    except ProviderError as exc:
        await _log_failure(name, model, started)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # noqa: BLE001 — surface any SDK/surprise error
        message = str(exc) or exc.__class__.__name__
        await _log_failure(name, model, started)
        raise HTTPException(status_code=502, detail=message) from exc

    prompt_tokens = result.get("prompt_tokens")
    completion_tokens = result.get("completion_tokens")
    cost_usd = await cost.estimate_cost(name, model, prompt_tokens, completion_tokens)

    await requestlog.log_request(
        provider=name,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost_usd=cost_usd,
        latency_ms=result.get("latency_ms"),
        kind=requestlog.KIND_TEXT,
    )

    return {
        "provider": name,
        "model": model,
        "text": result.get("text"),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": result.get("latency_ms"),
        "estimated_cost_usd": cost_usd,
    }


@router.post("/{provider}/search")
async def provider_search(provider: str, body: SearchBody) -> dict[str, Any]:
    """Run a search query (Tavily)."""
    name = _resolve_provider(provider)

    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    started = time.perf_counter()
    try:
        result = await PROVIDERS[name].search(body.query, body.options)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{name.title()} does not support search",
        ) from exc
    except ProviderError as exc:
        await _log_failure(name, "", started, kind=requestlog.KIND_SEARCH)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # noqa: BLE001
        message = str(exc) or exc.__class__.__name__
        await _log_failure(name, "", started, kind=requestlog.KIND_SEARCH)
        raise HTTPException(status_code=502, detail=message) from exc

    latency_ms = result.get("latency_ms")
    await requestlog.log_request(
        provider=name,
        model="",
        prompt_tokens=None,
        completion_tokens=None,
        estimated_cost_usd=None,
        latency_ms=latency_ms,
        kind=requestlog.KIND_SEARCH,
    )

    return {
        "provider": name,
        "text": result.get("text"),
        "prompt_tokens": None,
        "completion_tokens": None,
        "latency_ms": latency_ms,
    }


def _resolve_provider(provider: str) -> str:
    name = provider.lower()
    if name not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    return name


async def _log_failure(
    provider: str,
    model: str,
    started: float,
    kind: str = requestlog.KIND_TEXT,
) -> None:
    latency_ms = round((time.perf_counter() - started) * 1000)
    await requestlog.log_request(
        provider=provider,
        model=model,
        prompt_tokens=None,
        completion_tokens=None,
        estimated_cost_usd=None,
        latency_ms=latency_ms,
        kind=kind,
    )