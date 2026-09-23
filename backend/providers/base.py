"""
Abstract provider interface.

Every provider module must subclass :class:`BaseProvider` and implement the
shared interface.  The four methods below define the contract the router and
frontend rely on:

* ``health()``  -> ``{"status", "latency_ms", "error"}``
* ``models()``  -> normalized list of available models
* ``balance()`` -> balance/usage info, or ``None`` when unsupported
* ``request()`` -> response text plus token/latency metrics

Only ``health()`` is implemented in this phase.  ``health()`` itself is
implemented once here (shared latency / timeout / error handling) and delegates
the actual probe request to ``_probe()``, which each provider overrides.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

STATUS_OK = "ok"
STATUS_MISSING_KEY = "missing_key"
STATUS_TIMEOUT = "timeout"
STATUS_ERROR = "error"


class BaseProvider:
    """Base class all providers inherit from."""

    #: Lowercase identifier used in the /api/{provider}/health route.
    name: str = "base"

    #: Request timeout in seconds.
    timeout: float = 5.0

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
        if not self.api_key:
            return _result(STATUS_MISSING_KEY, None, "No API key configured")

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await self._probe(client)
        except httpx.TimeoutException:
            return _result(STATUS_TIMEOUT, None, "Request timed out")
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
        """Return a normalized list of available models."""
        raise NotImplementedError

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


def _result(status: str, latency_ms: int | None, error: str | None) -> dict[str, Any]:
    """Build the normalized health response dict."""
    return {"status": status, "latency_ms": latency_ms, "error": error}