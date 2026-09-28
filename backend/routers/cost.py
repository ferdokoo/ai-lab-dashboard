"""
Cost calculator route.

Exposes ``GET /api/cost`` which estimates the USD cost of a completion from the
cached pricing table.  An unknown provider returns 404; a known provider/model
with no cached price returns an honest ``estimated_cost_usd: null`` plus the
per-million prices/source the estimator did (or did not) find.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .. import cost
from ..providers import PROVIDERS

router = APIRouter(prefix="/api", tags=["cost"])


@router.get("/cost")
async def get_cost(
    provider: str,
    model: str,
    prompt_tokens: int = Query(default=0, ge=0),
    completion_tokens: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Estimate the cost of a completion using cached catalog pricing."""
    name = provider.lower()
    if name not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    model_id = model.strip()
    if not model_id:
        raise HTTPException(status_code=400, detail="Model is required")

    return await cost.estimate(name, model_id, prompt_tokens, completion_tokens)