"""
Health-check routes.

Exposes ``GET /api/{provider}/health`` for every registered provider.  The route
delegates to the provider's ``health()`` method and returns a normalized JSON
payload: ``{provider, status, latency_ms, error}``.

Also exposes ``GET /api/keys`` — the configured-key list with every key masked
down to its last four characters (never the full key).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..providers import PROVIDERS
from ..providers.base import mask_key

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


@router.get("/keys")
async def list_keys() -> dict[str, Any]:
    """Return each provider's key status with the key masked to its last four chars."""
    keys: list[dict[str, Any]] = []
    for name, impl in PROVIDERS.items():
        if not impl.requires_api_key:
            keys.append(
                {
                    "provider": name,
                    "configured": None,
                    "masked": None,
                    "note": "local provider — no key required",
                }
            )
            continue
        key = impl.api_key
        keys.append(
            {
                "provider": name,
                "configured": bool(key),
                "masked": mask_key(key),
            }
        )
    return {"keys": keys}