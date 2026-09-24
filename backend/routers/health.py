"""
Health-check routes.

Exposes ``GET /api/{provider}/health`` for every registered provider.  The route
delegates to the provider's ``health()`` method and returns a normalized JSON
payload: ``{provider, status, latency_ms, error}``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..providers import PROVIDERS

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/{provider}/health")
async def provider_health(provider: str) -> dict[str, Any]:
    """Run a health probe for the named provider."""
    impl = PROVIDERS.get(provider.lower())
    if impl is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    result = await impl.health()
    result["provider"] = provider.lower()
    return result