"""
Model-catalog routes.

Exposes ``GET /api/{provider}/models`` returning the normalized, priced model
list for a provider.  Results are cached in SQLite and re-fetched when
``?refresh=true`` is passed.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .. import cache, pricing
from ..providers import PROVIDERS
from ..providers.base import ProviderError

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/{provider}/models")
async def provider_models(provider: str, refresh: bool = False) -> dict[str, Any]:
    """Return the model catalog for the named provider."""
    impl = PROVIDERS.get(provider.lower())
    if impl is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    name = impl.name

    if not refresh:
        cached = await cache.get_catalog(name)
        if cached is not None:
            return {"provider": name, "models": cached, "cached": True}

    try:
        models = await impl.models()
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if not impl.supplies_pricing and impl.resolve_pricing:
        models = await pricing.resolve_missing_pricing(name, models)

    await cache.set_catalog(name, models)
    return {"provider": name, "models": models, "cached": False}