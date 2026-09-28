"""
Cost estimation.

Resolves the USD cost of a completion from the cached model-catalog pricing
(``backend.cache``).  The request runner, the cost calculator, and the broadcast
route all share this formula so estimates stay consistent.  A provider/model
without a cached price yields ``None`` rather than a fabricated zero (mission
principle 2 — honest data).
"""
from __future__ import annotations

from typing import Any

from . import cache


async def cached_pricing(provider: str, model: str) -> dict[str, Any] | None:
    """Return the cached catalog entry for ``model``, or ``None`` when absent."""
    models = await cache.get_catalog(provider) or []
    return next((m for m in models if m.get("id") == model), None)


def compute_cost(
    entry: dict[str, Any],
    prompt_tokens: int,
    completion_tokens: int,
) -> float | None:
    """Compute USD cost from a catalog entry and token counts, or ``None``.

    Returns ``None`` when the entry carries no per-million pricing at all.
    """
    input_price = entry.get("input_price_per_million")
    output_price = entry.get("output_price_per_million")
    if input_price is None and output_price is None:
        return None

    total = 0.0
    if input_price is not None:
        total += prompt_tokens / 1_000_000 * input_price
    if output_price is not None:
        total += completion_tokens / 1_000_000 * output_price
    return round(total, 8)


async def estimate_cost(
    provider: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    """Return the USD estimate, or ``None`` when unknown.

    ``None`` results from either unknown token counts or a missing cached price.
    """
    if prompt_tokens is None or completion_tokens is None:
        return None
    entry = await cached_pricing(provider, model)
    if entry is None:
        return None
    return compute_cost(entry, prompt_tokens, completion_tokens)


async def estimate(
    provider: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> dict[str, Any]:
    """Return full cost details: prices used, pricing source, and the estimate."""
    entry = await cached_pricing(provider, model)
    cost = (
        compute_cost(entry, prompt_tokens, completion_tokens)
        if entry is not None and prompt_tokens is not None and completion_tokens is not None
        else None
    )
    return {
        "provider": provider,
        "model": model,
        "input_price_per_million": entry.get("input_price_per_million") if entry else None,
        "output_price_per_million": entry.get("output_price_per_million") if entry else None,
        "pricing_source": entry.get("pricing_source") if entry else None,
        "estimated_cost_usd": cost,
    }