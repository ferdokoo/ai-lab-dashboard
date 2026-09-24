"""
Request-runner tests.

Covers the ``POST /api/{provider}/request`` and ``POST /api/{provider}/search``
routes plus the request-log writing behaviour using mocked providers — no live
network calls are made.
"""
from __future__ import annotations

import sqlite3
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.providers import PROVIDERS
from backend.providers.base import ProviderError


class StubProvider:
    """Configurable stand-in for a provider's ``request``/``search`` methods."""

    def __init__(
        self,
        name: str,
        request_result: dict[str, Any] | None = None,
        request_error: ProviderError | None = None,
        search_result: dict[str, Any] | None = None,
        search_error: ProviderError | None = None,
    ) -> None:
        self.name = name
        self._request_result = request_result
        self._request_error = request_error
        self._search_result = search_result
        self._search_error = search_error

    async def request(self, model, prompt, options=None):
        if self._request_error is not None:
            raise self._request_error
        return self._request_result

    async def search(self, query, options=None):
        if self._search_error is not None:
            raise self._search_error
        return self._search_result


@pytest.fixture
def client(tmp_db):
    return TestClient(app)


def read_requests(path) -> list[sqlite3.Row]:
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        has_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='requests'"
        ).fetchone()
        if has_table is None:
            return []
        return conn.execute(
            "SELECT provider, model, kind, prompt_tokens, completion_tokens, "
            "estimated_cost_usd, latency_ms FROM requests ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def test_openai_request_route_returns_normalized_payload(client, tmp_db, monkeypatch):
    """request route returns normalized payload"""
    stub = StubProvider(
        "openai",
        request_result={
            "text": "hello there",
            "prompt_tokens": 12,
            "completion_tokens": 7,
            "latency_ms": 134,
        },
    )
    monkeypatch.setitem(PROVIDERS, "openai", stub)

    response = client.post(
        "/api/openai/request",
        json={"model": "gpt-4o-mini", "prompt": "Say hi"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["text"] == "hello there"
    assert data["prompt_tokens"] == 12
    assert data["completion_tokens"] == 7
    assert data["latency_ms"] == 134


def test_request_log_row_written_on_success(client, tmp_db, monkeypatch):
    """request log row written on success"""
    stub = StubProvider(
        "openai",
        request_result={
            "text": "hello there",
            "prompt_tokens": 12,
            "completion_tokens": 7,
            "latency_ms": 134,
        },
    )
    monkeypatch.setitem(PROVIDERS, "openai", stub)

    client.post("/api/openai/request", json={"model": "gpt-4o-mini", "prompt": "Say hi"})

    rows = read_requests(tmp_db)
    assert len(rows) == 1
    row = rows[0]
    assert row["provider"] == "openai"
    assert row["model"] == "gpt-4o-mini"
    assert row["kind"] == "text"
    assert row["prompt_tokens"] == 12
    assert row["completion_tokens"] == 7
    assert row["latency_ms"] is not None
    # No prompt/response body is ever written — the schema has no such column.
    columns = [c[1] for c in sqlite3.connect(tmp_db).execute("PRAGMA table_info(requests)")]
    assert not any("body" in c or "prompt_text" in c for c in columns)


def test_request_log_written_on_failure(client, tmp_db, monkeypatch):
    """request log written on failure"""
    stub = StubProvider(
        "openai",
        request_error=ProviderError("Invalid API key", status_code=401),
    )
    monkeypatch.setitem(PROVIDERS, "openai", stub)

    response = client.post(
        "/api/openai/request", json={"model": "gpt-4o-mini", "prompt": "Say hi"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"

    rows = read_requests(tmp_db)
    assert len(rows) == 1
    assert rows[0]["provider"] == "openai"
    assert rows[0]["kind"] == "text"
    assert rows[0]["prompt_tokens"] is None
    assert rows[0]["completion_tokens"] is None
    assert rows[0]["latency_ms"] is not None


def test_empty_prompt_is_rejected_without_writing(client, tmp_db, monkeypatch):
    """empty prompt rejected without logging"""
    stub = StubProvider(
        "openai",
        request_result={"text": "", "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 1},
    )
    monkeypatch.setitem(PROVIDERS, "openai", stub)

    response = client.post(
        "/api/openai/request", json={"model": "gpt-4o-mini", "prompt": "   "}
    )

    assert response.status_code == 400
    assert read_requests(tmp_db) == []


def test_unknown_provider_returns_404(client):
    """unknown provider returns 404"""
    response = client.post(
        "/api/nope/request", json={"model": "m", "prompt": "hi"}
    )
    assert response.status_code == 404


def test_tavily_search_route_logs_distinctly(client, tmp_db, monkeypatch):
    """tavily search route logs distinctly"""
    stub = StubProvider(
        "tavily",
        search_result={
            "text": "Search results here",
            "prompt_tokens": None,
            "completion_tokens": None,
            "latency_ms": 88,
        },
    )
    monkeypatch.setitem(PROVIDERS, "tavily", stub)

    response = client.post("/api/tavily/search", json={"query": "what is sqlite"})

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Search results here"
    assert data["prompt_tokens"] is None
    assert data["completion_tokens"] is None
    assert data["latency_ms"] == 88

    rows = read_requests(tmp_db)
    assert len(rows) == 1
    assert rows[0]["provider"] == "tavily"
    assert rows[0]["kind"] == "search"
    assert rows[0]["model"] == ""
    assert rows[0]["prompt_tokens"] is None
    assert rows[0]["completion_tokens"] is None


def test_tavily_request_route_is_rejected(client):
    """tavily request route is rejected"""
    response = client.post(
        "/api/tavily/request", json={"model": "x", "prompt": "hi"}
    )
    assert response.status_code == 400


def test_empty_search_query_is_rejected(client, tmp_db, monkeypatch):
    """empty search query rejected without logging"""
    stub = StubProvider(
        "tavily",
        search_result={"text": "", "prompt_tokens": None, "completion_tokens": None, "latency_ms": 1},
    )
    monkeypatch.setitem(PROVIDERS, "tavily", stub)

    response = client.post("/api/tavily/search", json={"query": " "})
    assert response.status_code == 400
    assert read_requests(tmp_db) == []


# --- Provider-level tests with mocked SDKs -----------------------------------


@pytest.mark.asyncio
async def test_openai_provider_request_normalized(monkeypatch):
    """openai provider normalizes request"""
    import openai
    from backend.providers.openai import provider as openai_provider

    class FakeMessage:
        content = "hello from openai"

    class FakeChoice:
        message = FakeMessage()

    class FakeUsage:
        prompt_tokens = 11
        completion_tokens = 9

    class FakeResponse:
        usage = FakeUsage()
        choices = [FakeChoice()]

    class FakeCompletions:
        async def create(self, **kwargs):
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(openai, "AsyncOpenAI", FakeAsyncOpenAI)

    result = await openai_provider.request("gpt-4o-mini", "Say hi")

    assert result["text"] == "hello from openai"
    assert result["prompt_tokens"] == 11
    assert result["completion_tokens"] == 9
    assert isinstance(result["latency_ms"], int)


@pytest.mark.asyncio
async def test_anthropic_provider_request_normalized(monkeypatch):
    """anthropic provider normalizes request"""
    import anthropic
    from backend.providers.anthropic import provider as anthropic_provider

    class FakeTextBlock:
        type = "text"
        text = "hello from anthropic"

    class FakeUsage:
        input_tokens = 15
        output_tokens = 3

    class FakeMessage:
        content = [FakeTextBlock()]
        usage = FakeUsage()

    class FakeMessages:
        async def create(self, **kwargs):
            return FakeMessage()

    class FakeAsyncAnthropic:
        def __init__(self, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr(anthropic, "AsyncAnthropic", FakeAsyncAnthropic)

    result = await anthropic_provider.request("claude-3-5-sonnet-latest", "Say hi")

    assert result["text"] == "hello from anthropic"
    assert result["prompt_tokens"] == 15
    assert result["completion_tokens"] == 3
    assert isinstance(result["latency_ms"], int)


@pytest.mark.asyncio
async def test_tavily_search_returns_honest_none_tokens(monkeypatch):
    """tavily search reports None token counts"""
    import httpx
    from backend.config import settings
    from backend.providers.tavily import provider as tavily_provider

    class FakeHttpResponse:
        status_code = 200

        def json(self):
            return {
                "answer": "SQLite is a database.",
                "results": [
                    {"title": "SQLite", "url": "https://sqlite.org", "content": "A small DB"}
                ],
            }

    class FakeClient:
        def __init__(self, timeout=None):
            self.sent = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            self.sent = json
            return FakeHttpResponse()

    monkeypatch.setattr(settings, "tavily_api_key", "test-key")
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    result = await tavily_provider.search("what is sqlite", {"max_results": 3})

    assert "SQLite is a database." in result["text"]
    assert "https://sqlite.org" in result["text"]
    assert result["prompt_tokens"] is None
    assert result["completion_tokens"] is None
    assert isinstance(result["latency_ms"], int)