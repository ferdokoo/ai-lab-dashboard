"""
Balance & usage tests.

Covers the ``GET /api/{provider}/balance`` route and the provider ``balance()``
methods using mocked ``httpx.AsyncClient`` and stubbed providers — no live
network calls.  Verifies real-data normalization (OpenRouter, Tavily), the
honest "not available" fallback (OpenAI, Anthropic, Gemini, local), and the
OpenRouter management-key requirement.
"""
from __future__ import annotations

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
from backend.providers import PROVIDERS
from backend.providers.anthropic import provider as anthropic_provider
from backend.providers.gemini import provider as gemini_provider
from backend.providers.openai import provider as openai_provider
from backend.providers.openrouter import provider as openrouter_provider
from backend.providers.tavily import provider as tavily_provider
from backend.providers.base import ProviderError


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self) -> Any:
        return self._payload


class FakeClient:
    """httpx.AsyncClient stand-in returning a canned GET response."""

    def __init__(self, timeout: float | None = None) -> None:
        self.timeout = timeout
        self.response = FakeResponse()
        self.get_calls: list[tuple[str, dict[str, Any]]] = []

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *args: Any) -> bool:
        return False

    async def get(self, url: str, headers: dict[str, Any] | None = None, **kwargs: Any) -> FakeResponse:
        self.get_calls.append((url, headers or {}))
        return self.response


class StubBalanceProvider:
    """Stub provider whose ``balance()`` returns a fixed value or raises."""

    def __init__(self, name: str, result: Any = None, error: ProviderError | None = None,
                 billing_url: str | None = None) -> None:
        self.name = name
        self._result = result
        self._error = error
        self.billing_url = billing_url

    async def balance(self) -> Any:
        if self._error is not None:
            raise self._error
        return self._result


# --- Provider-level balance() tests -----------------------------------------


@pytest.mark.asyncio
async def test_openrouter_balance_normalized(monkeypatch):
    """openrouter balance normalizes credits and computes remaining"""
    client = FakeClient()
    client.response = FakeResponse(200, {
        "data": {"total_credits": 100.0, "total_usage": 23.5}
    })
    monkeypatch.setattr(settings, "openrouter_management_key", "mgmt-key")
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    result = await openrouter_provider.balance()

    assert result["fields"]["total_credits"] == 100.0
    assert result["fields"]["total_usage"] == 23.5
    assert result["fields"]["credit_remaining"] == 76.5
    assert result["raw"]["total_credits"] == 100.0
    assert client.get_calls[0][1]["Authorization"] == "Bearer mgmt-key"


@pytest.mark.asyncio
async def test_openrouter_balance_requires_management_key(monkeypatch):
    """openrouter balance reports a missing management key"""
    monkeypatch.setattr(settings, "openrouter_management_key", None)

    with pytest.raises(ProviderError) as exc:
        await openrouter_provider.balance()

    assert "management key" in exc.value.message
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_tavily_balance_normalized(monkeypatch):
    """tavily balance normalizes key and account usage"""
    client = FakeClient()
    client.response = FakeResponse(200, {
        "key": {"usage": 12, "limit": 1000},
        "account": {"plan": "free", "usage": 3, "limit": 1000},
    })
    monkeypatch.setattr(settings, "tavily_api_key", "tavily-key")
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    result = await tavily_provider.balance()

    assert result["fields"]["plan"] == "free"
    assert result["fields"]["key_usage"] == 12
    assert result["fields"]["account_limit"] == 1000
    assert result["raw"]["key"]["limit"] == 1000


@pytest.mark.asyncio
async def test_unsupported_providers_return_none():
    """openai, anthropic, and gemini balance() return None"""
    for provider in (openai_provider, anthropic_provider, gemini_provider):
        assert await provider.balance() is None
        assert provider.billing_url is not None


@pytest.mark.asyncio
async def test_local_providers_return_none(monkeypatch):
    """local providers report None balance with no billing url"""
    from backend.providers.ollama import provider as ollama_provider
    from backend.providers.lmstudio import provider as lmstudio_provider

    for provider in (ollama_provider, lmstudio_provider):
        assert await provider.balance() is None
        assert provider.billing_url is None


# --- Route tests -------------------------------------------------------------


@pytest.fixture
def client(tmp_db):
    return TestClient(app)


def test_balance_route_supported(client, monkeypatch):
    """balance route returns normalized result for a supported provider"""
    stub = StubBalanceProvider(
        "openrouter",
        result={"fields": {"total_credits": 100.0, "total_usage": 0.0}, "raw": {}},
    )
    monkeypatch.setitem(PROVIDERS, "openrouter", stub)

    response = client.get("/api/openrouter/balance")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openrouter"
    assert data["supported"] is True
    assert data["fields"]["total_credits"] == 100.0


def test_balance_route_unsupported_with_billing_link(client, monkeypatch):
    """balance route returns honest fallback with billing link"""
    stub = StubBalanceProvider(
        "openai", result=None, billing_url="https://platform.openai.com/billing"
    )
    monkeypatch.setitem(PROVIDERS, "openai", stub)

    response = client.get("/api/openai/balance")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["supported"] is False
    assert "not available" in data["message"]
    assert data["billing_url"] == "https://platform.openai.com/billing"


def test_balance_route_local_no_billing_link(client, monkeypatch):
    """balance route for local providers omits the billing link"""
    stub = StubBalanceProvider("ollama", result=None, billing_url=None)
    monkeypatch.setitem(PROVIDERS, "ollama", stub)

    response = client.get("/api/ollama/balance")

    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is False
    assert data["billing_url"] is None


def test_balance_route_provider_error(client, monkeypatch):
    """balance route surfaces a ProviderError as an HTTP error"""
    stub = StubBalanceProvider(
        "openrouter",
        error=ProviderError("OpenRouter management key not configured", status_code=400),
    )
    monkeypatch.setitem(PROVIDERS, "openrouter", stub)

    response = client.get("/api/openrouter/balance")

    assert response.status_code == 400
    assert "management key" in response.json()["detail"]


def test_balance_route_unknown_provider(client):
    """balance route returns 404 for an unknown provider"""
    response = client.get("/api/nope/balance")
    assert response.status_code == 404