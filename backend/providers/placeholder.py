"""
Placeholder provider — establishes the shared interface shape.

Every real provider module must implement these four methods.
This module raises NotImplementedError on every call so that any accidental
import at runtime fails loudly rather than silently doing nothing.
"""
from __future__ import annotations

from typing import Any


class PlaceholderProvider:
    """Stub provider.  Replace with a concrete implementation per provider."""

    def health(self) -> dict[str, Any]:
        """Return a health status dict (status, latency_ms)."""
        raise NotImplementedError

    def models(self) -> list[dict[str, Any]]:
        """Return a normalised list of available models."""
        raise NotImplementedError

    def balance(self) -> dict[str, Any] | None:
        """Return balance/usage info, or None if the provider doesn't support it."""
        raise NotImplementedError

    def request(
        self,
        model: str,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a prompt and return response text plus usage metrics."""
        raise NotImplementedError
