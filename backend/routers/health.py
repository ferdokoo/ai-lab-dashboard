"""
Health-check routes.

Exposes ``GET /api/{provider}/health`` for every registered provider.  The route
delegates to the provider's ``health()`` method and returns a normalized JSON
payload: ``{provider, status, latency_ms, error}``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..providers import anthropic, gemini, openai, openrouter, tavily
from ..providers.base import BaseProvider

router = APIRouter(prefix="/api", tags=["health"])

_PROVIDERS: dict[str, BaseProvider] = {
    openai.provider.name: openai.provider,
    anthropic.provider.name: anthropic.provider,
    gemini.provider.name: gemini.provider,
    openrouter.provider.name: openrouter.provider,
    tavily.provider.name: tavily.provider,
}


@router.get("/{provider}/health")
async def provider_health(provider: str) -> dict[str, Any]:
    """Run a health probe for the named provider."""
    impl = _PROVIDERS.get(provider.lower())
    if impl is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    result = await impl.health()
    result["provider"] = provider.lower()
    return result