"""
Broadcast / compare-mode route.

``POST /api/broadcast`` sends one prompt to multiple provider/model pairs
concurrently and returns one result per target.  A failing target (missing key,
API error, offline local server) is reported inline in its own ``error`` entry
so one failure never blocks the others.  Only counts, latency, and estimated
cost are logged — never prompt/response bodies (mission principle 3).
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import cost, requestlog
from ..providers import PROVIDERS
from ..providers.base import ProviderError

router = APIRouter(prefix="/api", tags=["broadcast"])

#: Providers whose action is a search rather than an LLM completion.
_SEARCH_ONLY = {"tavily"}


class BroadcastTarget(BaseModel):
    provider: str
    model: str


class BroadcastBody(BaseModel):
    prompt: str
    targets: list[BroadcastTarget]
    options: dict[str, Any] = Field(default_factory=dict)


_MAX_TARGETS = 10


@router.post("/broadcast")
async def broadcast(body: BroadcastBody) -> dict[str, Any]:
    """Fan out one prompt to every target concurrently and collect results."""
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    if not body.targets:
        raise HTTPException(status_code=400, detail="At least one target is required")
    if len(body.targets) > _MAX_TARGETS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many targets: maximum is {_MAX_TARGETS}",
        )

    results = await asyncio.gather(
        *(_run_target(target, body.prompt, body.options) for target in body.targets)
    )
    return {"results": list(results)}


async def _run_target(
    target: BroadcastTarget,
    prompt: str,
    options: dict[str, Any],
) -> dict[str, Any]:
    """Run a single target and normalize success or failure into one dict."""
    name = target.provider.lower()
    model = target.model.strip()

    if name not in PROVIDERS:
        return {"provider": name, "model": model, "error": f"Unknown provider: {name}"}

    if name in _SEARCH_ONLY:
        return {
            "provider": name,
            "model": model,
            "error": f"{name.title()} is a search provider and is not supported for broadcast",
        }

    if not model:
        return {"provider": name, "model": model, "error": "Model is required"}

    started = time.perf_counter()
    try:
        result = await PROVIDERS[name].request(model, prompt, options)
    except ProviderError as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        await _log_target(name, model, None, None, latency_ms)
        return {"provider": name, "model": model, "error": exc.message, "latency_ms": latency_ms}
    except Exception as exc:  # noqa: BLE001 — surface any SDK/surprise error
        message = str(exc) or exc.__class__.__name__
        latency_ms = round((time.perf_counter() - started) * 1000)
        await _log_target(name, model, None, None, latency_ms)
        return {"provider": name, "model": model, "error": message, "latency_ms": latency_ms}

    prompt_tokens = result.get("prompt_tokens")
    completion_tokens = result.get("completion_tokens")
    cost_usd = await cost.estimate_cost(name, model, prompt_tokens, completion_tokens)

    await _log_target(
        name,
        model,
        prompt_tokens,
        completion_tokens,
        result.get("latency_ms"),
        cost_usd,
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


async def _log_target(
    provider: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    latency_ms: int | None,
    estimated_cost_usd: float | None = None,
) -> None:
    await requestlog.log_request(
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost_usd=estimated_cost_usd,
        latency_ms=latency_ms,
        kind=requestlog.KIND_TEXT,
    )