"""
Pricing resolution for the model catalog.

Providers whose ``/models`` API returns price data (OpenRouter) already merge
it into their normalized entries.  Providers whose API does not return pricing
(OpenAI, Anthropic, Gemini) have their top models priced here via the Tavily
search tool, which is queried over ``httpx`` like every other probe.

We never fabricate a price: if the search returns nothing we can parse
reliably, the price field stays ``None`` (the "Honest data" principle).
"""
from __future__ import annotations

import re
from typing import Any

import httpx

from .config import settings

_SEARCH_URL = "https://api.tavily.com/search"

#: Only the first few unpriced models are looked up to keep the catalog fast.
_TOP_MODEL_COUNT = 5

#: Ordered paired patterns that capture input and output prices together, so
#: two distinct dollar amounts are guaranteed.  Each pattern captures the input
#: price in group 1 and the output price in group 2.
_PAIRED_PATTERNS: tuple[re.Pattern[str], ...] = (
    # "input ... $A ... output ... $B"
    re.compile(
        r"input\b[^$]{0,60}?\$([0-9]+(?:\.[0-9]+)?)[\s\S]{0,240}?output\b[^$]{0,60}?\$([0-9]+(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
    # "$A ... input ... $B ... output"
    re.compile(
        r"\$([0-9]+(?:\.[0-9]+)?)[^$]{0,40}?input\b[\s\S]{0,240}?\$([0-9]+(?:\.[0-9]+)?)[^$]{0,40}?output\b",
        re.IGNORECASE,
    ),
    # "input ... $A ... $B ... output"
    re.compile(
        r"input\b[^$]{0,60}?\$([0-9]+(?:\.[0-9]+)?)[^$]{0,80}?\$([0-9]+(?:\.[0-9]+)?)[\s\S]{0,60}?output\b",
        re.IGNORECASE,
    ),
)


async def resolve_missing_pricing(
    provider: str, models: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Fill in pricing for a provider's top models via Tavily search.

    Only entries without a ``pricing_source`` are considered; the first
    :data:`_TOP_MODEL_COUNT` of them are searched.  Missing Tavily key or failed
    lookups leave the entry's pricing fields ``None``.
    """
    if not settings.tavily_api_key:
        return models

    unpriced = [m for m in models if m.get("pricing_source") is None][:_TOP_MODEL_COUNT]
    for model in unpriced:
        prices = await _search_model_pricing(provider, model["id"])
        if prices is not None:
            model["input_price_per_million"] = prices["input"]
            model["output_price_per_million"] = prices["output"]
            model["pricing_source"] = "tavily"
    return models


async def _search_model_pricing(provider: str, model_id: str) -> dict[str, float] | None:
    query = f"{model_id} API pricing input output cost per 1M tokens"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                _SEARCH_URL,
                headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
                json={"query": query, "max_results": 5, "search_depth": "advanced"},
            )
    except (httpx.TimeoutException, httpx.RequestError):
        return None
    if response.status_code >= 300:
        return None

    return _parse_prices(response.json())


def _parse_prices(data: dict[str, Any]) -> dict[str, float] | None:
    """Extract input/output USD prices from Tavily search results, if reliably present."""
    chunks: list[str] = [""]
    for result in data.get("results", []):
        chunks.append(result.get("title") or "")
        chunks.append(result.get("content") or "")

    for chunk in chunks:
        for pattern in _PAIRED_PATTERNS:
            match = pattern.search(chunk)
            if not match:
                continue
            input_price = float(match.group(1))
            output_price = float(match.group(2))
            if input_price <= 0 or output_price <= 0:
                continue
            # Output tokens are almost always at least as expensive as input.
            # A reversed pair is a near-certain sign the two were swapped.
            if input_price > output_price:
                input_price, output_price = output_price, input_price
            return {"input": input_price, "output": output_price}
    return None