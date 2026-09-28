"""
Abstract provider interface.

Every provider module must subclass :class:`BaseProvider` and implement the
shared interface.  The four methods below define the contract the router and
frontend rely on:

* ``health()``  -> ``{"status", "latency_ms", "error"}``
* ``models()``  -> normalized list of available models
* ``balance()`` -> balance/usage info, or ``None`` when unsupported
* ``request()`` -> response text plus token/latency metrics
* ``search()``  -> search-text response (Tavily), token metrics ``None``

``health()`` is implemented once here (shared latency / timeout / error
handling) and delegates the actual probe request to ``_probe()``, which each
provider overrides.

``models()`` returns a list of normalized entries, each with the shape::

    {
        "id": str,
        "context_window": int | None,
        "input_price_per_million": float | None,
        "output_price_per_million": float | None,
        "pricing_source": "api" | "tavily" | None,
    }
"""
from __future__ import annotations

import time
from typing import Any

import httpx

STATUS_OK = "ok"
STATUS_MISSING_KEY = "missing_key"
STATUS_TIMEOUT = "timeout"
STATUS_ERROR = "error"


class ProviderError(Exception):
    """Raised when a provider cannot service a call (missing key, API error)."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BaseProvider:
    """Base class all providers inherit from."""

    #: Lowercase identifier used in the /api/{provider}/health route.
    name: str = "base"

    #: Request timeout in seconds.
    timeout: float = 5.0

    #: Whether the provider's ``models()`` response already carries pricing.
    #: When ``False``, the router resolves top-model prices via Tavily search.
    supplies_pricing: bool = False

    #: Whether the provider needs an API key to operate.  Local providers
    #: (Ollama, LM Studio) set this ``False``.
    requires_api_key: bool = True

    #: Whether missing pricing should be resolved via Tavily search.  Local
    #: providers set this ``False`` — their models have no public pricing.
    resolve_pricing: bool = True

    @property
    def api_key(self) -> str | None:
        """Return the provider API key from config, or ``None`` if unset."""
        return None

    async def health(self) -> dict[str, Any]:
        """Probe the provider with its cheapest valid call.

        Returns:
            A dict with the following keys:

            * ``status``     -- one of ``"ok"``, ``"missing_key"``,
                                ``"timeout"``, ``"error"``
            * ``latency_ms`` -- integer milliseconds on ``"ok"``/``"error"``,
                                otherwise ``None``
            * ``error``      -- human-readable message on failure, else ``None``
        """
        if self.requires_api_key and not self.api_key:
            return _result(STATUS_MISSING_KEY, None, "No API key configured")

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await self._probe(client)
        except httpx.TimeoutException:
            return _result(STATUS_TIMEOUT, None, "Request timed out")
        except httpx.ConnectError as exc:
            return _result(STATUS_ERROR, None, f"Connection failed: {exc}")
        except httpx.RequestError as exc:
            return _result(STATUS_ERROR, None, f"Request failed: {exc}")

        latency_ms = round((time.perf_counter() - started) * 1000)
        if response.status_code < 300:
            return _result(STATUS_OK, latency_ms, None)
        return _result(STATUS_ERROR, latency_ms, f"HTTP {response.status_code}")

    async def _probe(self, client: httpx.AsyncClient) -> httpx.Response:
        """Issue the provider's cheapest probe request.

        Subclasses override this; the base ``health()`` handles authentication,
        latency measurement, and error mapping around it.
        """
        raise NotImplementedError

    async def models(self) -> list[dict[str, Any]]:
        """Return a normalized list of available models.

        Each entry uses :func:`model_entry` shape (``id``, ``context_window``,
        ``input_price_per_million``, ``output_price_per_million``,
        ``pricing_source``).  Pricing included by the API is merged here;
        providers without API pricing leave those fields ``None``.
        """
        raise NotImplementedError

    async def _list_models(self) -> httpx.Response:
        """Fetch the provider's model list, validating the key and mapping errors.

        Reuses ``_probe()`` for the actual request and converts failures into
        :class:`ProviderError` so the router can surface a clear HTTP response.
        """
        if self.requires_api_key and not self.api_key:
            raise ProviderError(f"No {self.name} API key configured", status_code=401)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await self._probe(client)
        except httpx.TimeoutException:
            raise ProviderError("Request timed out") from None
        except httpx.ConnectError as exc:
            raise ProviderError(f"Connection failed: {exc}") from None
        except httpx.RequestError as exc:
            raise ProviderError(f"Request failed: {exc}") from None
        if response.status_code >= 300:
            raise ProviderError(f"HTTP {response.status_code}")
        return response

    async def balance(self) -> dict[str, Any] | None:
        """Return balance/usage info, or ``None`` when the provider doesn't expose it."""
        raise NotImplementedError

    async def request(
        self,
        model: str,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a prompt and return response text plus usage metrics."""
        raise NotImplementedError

    async def search(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a search query and return result text (token metrics ``None``)."""
        raise NotImplementedError


def _result(status: str, latency_ms: int | None, error: str | None) -> dict[str, Any]:
    """Build the normalized health response dict."""
    return {"status": status, "latency_ms": latency_ms, "error": error}


def request_result(
    text: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    latency_ms: int,
) -> dict[str, Any]:
    """Build the normalized request response dict."""
    return {
        "text": text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": latency_ms,
    }


def model_entry(
    model_id: str,
    context_window: int | None = None,
    input_price_per_million: float | None = None,
    output_price_per_million: float | None = None,
    pricing_source: str | None = None,
) -> dict[str, Any]:
    """Build one normalized model-catalog entry."""
    return {
        "id": model_id,
        "context_window": context_window,
        "input_price_per_million": input_price_per_million,
        "output_price_per_million": output_price_per_million,
        "pricing_source": pricing_source,
    }