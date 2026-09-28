"""
Balance & usage routes.

Exposes ``GET /api/{provider}/balance`` for every registered provider.  The
route delegates to the provider's ``balance()`` method:

* Providers whose API surfaces credit/usage data (OpenRouter, Tavily) return a
  normalized ``fields`` mapping plus the provider's raw response.
* Providers with no balance endpoint (OpenAI, Anthropic, Gemini) and local
  providers (Ollama, LM Studio) return an honest ``supported: false`` payload
  with a billing link where one exists — never a placeholder or guessed value.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..providers import PROVIDERS
from ..providers.base import ProviderError

router = APIRouter(prefix="/api", tags=["balance"])


@router.get("/{provider}/balance")
async def provider_balance(provider: str) -> dict[str, Any]:
    """Return balance/usage info for the named provider, or an honest fallback."""
    impl = PROVIDERS.get(provider.lower())
    if impl is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    name = impl.name

    try:
        result = await impl.balance()
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if result is None:
        return {
            "provider": name,
            "supported": False,
            "message": (
                f"Balance is not available via the {name.title()} API"
                if impl.billing_url
                else f"{name.title()} is a local provider — no balance to report"
            ),
            "billing_url": impl.billing_url,
        }

    return {"provider": name, "supported": True, **result}