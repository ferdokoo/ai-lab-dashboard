"""
Local-inference provider tests (Ollama + LM Studio).

Covers ``health()``, ``models()``, and ``request()`` for both local providers
using a monkeypatched ``httpx.AsyncClient`` — no live servers or real network
calls.  Also verifies the providers are registered with no API-key requirement.
"""
from __future__ import annotations

from typing import Any

import httpx
import pytest

from backend.providers import PROVIDERS
from backend.providers.lmstudio import provider as lmstudio_provider
from backend.providers.ollama import provider as ollama_provider
from backend.providers.base import ProviderError


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self) -> Any:
        return self._payload


class FakeClient:
    """httpx.AsyncClient stand-in returning canned responses per verb."""

    def __init__(self, timeout: float | None = None) -> None:
        self.received: list[tuple] = []
        self.on_get: Any = None
        self.on_post: Any = None

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *args: Any) -> bool:
        return False

    async def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.received.append(("get", url))
        return self.on_get(url)

    async def post(self, url: str, json: Any = None, **kwargs: Any) -> FakeResponse:
        self.received.append(("post", url, json))
        return self.on_post(url, json)


def _down_client() -> FakeClient:
    client = FakeClient()

    def fail(_url: str, *_rest: Any) -> FakeResponse:
        raise httpx.ConnectError("connection refused", request=None)

    client.on_get = lambda url: fail(url)
    client.on_post = lambda url, json: fail(url, json)
    return client


# --- Registration ------------------------------------------------------------


def test_local_providers_are_registered_without_api_key():
    """ollama and lmstudio are registered and require no API key"""
    for name in ("ollama", "lmstudio"):
        assert name in PROVIDERS
        assert PROVIDERS[name].requires_api_key is False


# --- Ollama ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ollama_health_ok(monkeypatch):
    """ollama health returns ok when the server responds"""
    client = FakeClient()
    client.on_get = lambda url: FakeResponse(200, {"models": []})
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    result = await ollama_provider.health()

    assert result["status"] == "ok"
    assert isinstance(result["latency_ms"], int)
    assert result["error"] is None


@pytest.mark.asyncio
async def test_ollama_health_connection_failure(monkeypatch):
    """ollama health surfaces a clear connection error when the server is down"""
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: _down_client())

    result = await ollama_provider.health()

    assert result["status"] == "error"
    assert "Connection failed" in result["error"]
    assert result["latency_ms"] is None


@pytest.mark.asyncio
async def test_ollama_models_normalized(monkeypatch):
    """ollama model list is normalized to the shared shape"""
    client = FakeClient()
    client.on_get = lambda url: FakeResponse(
        200, {"models": [{"name": "llama3:latest"}, {"name": "mistral:7b"}]}
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    models = await ollama_provider.models()

    assert [m["id"] for m in models] == ["llama3:latest", "mistral:7b"]
    assert all(m["pricing_source"] is None for m in models)


@pytest.mark.asyncio
async def test_ollama_request_normalized(monkeypatch):
    """ollama request maps eval counts onto token usage"""
    client = FakeClient()
    client.on_post = lambda url, json: FakeResponse(
        200,
        {
            "response": "hello from ollama",
            "prompt_eval_count": 11,
            "eval_count": 7,
        },
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    result = await ollama_provider.request("llama3:latest", "Say hi")

    assert result["text"] == "hello from ollama"
    assert result["prompt_tokens"] == 11
    assert result["completion_tokens"] == 7
    assert isinstance(result["latency_ms"], int)
    assert client.received[0][0] == "post"
    assert client.received[0][2]["stream"] is False


@pytest.mark.asyncio
async def test_ollama_request_connection_failure(monkeypatch):
    """ollama request raises a clear ProviderError when down"""
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: _down_client())

    with pytest.raises(ProviderError) as exc:
        await ollama_provider.request("llama3:latest", "Say hi")

    assert "Connection failed" in exc.value.message
    assert exc.value.status_code == 502


# --- LM Studio ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_lmstudio_health_ok(monkeypatch):
    """lmstudio health returns ok when the server responds"""
    client = FakeClient()
    client.on_get = lambda url: FakeResponse(200, {"data": []})
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    result = await lmstudio_provider.health()

    assert result["status"] == "ok"
    assert isinstance(result["latency_ms"], int)


@pytest.mark.asyncio
async def test_lmstudio_health_connection_failure(monkeypatch):
    """lmstudio health surfaces a clear connection error when the server is down"""
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: _down_client())

    result = await lmstudio_provider.health()

    assert result["status"] == "error"
    assert "Connection failed" in result["error"]


@pytest.mark.asyncio
async def test_lmstudio_models_normalized(monkeypatch):
    """lmstudio model list is normalized to the shared shape"""
    client = FakeClient()
    client.on_get = lambda url: FakeResponse(
        200, {"data": [{"id": "local-model-a"}, {"id": "local-model-b"}]}
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    models = await lmstudio_provider.models()

    assert [m["id"] for m in models] == ["local-model-a", "local-model-b"]
    assert all(m["pricing_source"] is None for m in models)


@pytest.mark.asyncio
async def test_lmstudio_request_normalized(monkeypatch):
    """lmstudio request maps OpenAI-compatible usage onto token counts"""
    client = FakeClient()
    client.on_post = lambda url, json: FakeResponse(
        200,
        {
            "choices": [{"message": {"role": "assistant", "content": "hello from lm studio"}}],
            "usage": {"prompt_tokens": 9, "completion_tokens": 5},
        },
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: client)

    result = await lmstudio_provider.request("local-model-a", "Say hi")

    assert result["text"] == "hello from lm studio"
    assert result["prompt_tokens"] == 9
    assert result["completion_tokens"] == 5
    assert isinstance(result["latency_ms"], int)


@pytest.mark.asyncio
async def test_lmstudio_request_connection_failure(monkeypatch):
    """lmstudio request raises a clear ProviderError when down"""
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=None: _down_client())

    with pytest.raises(ProviderError) as exc:
        await lmstudio_provider.request("local-model-a", "Say hi")

    assert "Connection failed" in exc.value.message
    assert exc.value.status_code == 502