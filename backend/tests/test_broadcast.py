"""
Broadcast / compare-mode tests.

Covers ``POST /api/broadcast`` with mocked providers — no live network calls.
Verifies concurrent fan-out, per-target failure isolation, validation of the
prompt/target list, and that only counts/latency/cost (never bodies) are logged.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.main import app
from backend.providers import PROVIDERS
from backend.providers.base import ProviderError


class StubProvider:
    """Configurable stand-in for a provider's ``request`` method."""

    def __init__(
        self,
        name: str,
        result: dict[str, Any] | None = None,
        error: ProviderError | None = None,
    ) -> None:
        self.name = name
        self._result = result
        self._error = error

    async def request(self, model, prompt, options=None):
        if self._error is not None:
            raise self._error
        return self._result


def ok_result(text="hello", prompt_tokens=12, completion_tokens=7, latency_ms=134):
    return {
        "text": text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": latency_ms,
    }


def seed_catalog(tmp_db, provider, models):
    asyncio.run(db.ensure_schema())
    conn = sqlite3.connect(tmp_db)
    try:
        conn.execute(
            "INSERT INTO catalog (provider, data, fetched_at) VALUES (?, ?, ?)",
            (provider, json.dumps(models), "2026-09-28T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()


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


@pytest.fixture
def client(tmp_db):
    return TestClient(app)


def test_broadcast_fans_out_and_returns_all_results(client, monkeypatch):
    """broadcast fans out to every target and returns one result per target"""
    monkeypatch.setitem(PROVIDERS, "openai", StubProvider("openai", result=ok_result(text="a")))
    monkeypatch.setitem(PROVIDERS, "anthropic", StubProvider("anthropic", result=ok_result(text="b")))

    response = client.post(
        "/api/broadcast",
        json={
            "prompt": "say hi",
            "targets": [
                {"provider": "openai", "model": "gpt-4o-mini"},
                {"provider": "anthropic", "model": "claude"},
            ],
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    assert any(r["provider"] == "openai" and r["text"] == "a" for r in results)
    assert any(r["provider"] == "anthropic" and r["text"] == "b" for r in results)


def test_broadcast_isolates_failing_target(client, monkeypatch, tmp_db):
    """broadcast reports a failing target inline without blocking siblings"""
    monkeypatch.setitem(PROVIDERS, "openai", StubProvider("openai", result=ok_result(text="ok")))
    monkeypatch.setitem(
        PROVIDERS,
        "anthropic",
        StubProvider("anthropic", error=ProviderError("Invalid API key", status_code=401)),
    )

    response = client.post(
        "/api/broadcast",
        json={
            "prompt": "say hi",
            "targets": [
                {"provider": "openai", "model": "gpt-4o-mini"},
                {"provider": "anthropic", "model": "claude"},
            ],
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2

    openai_result = next(r for r in results if r["provider"] == "openai")
    assert "error" not in openai_result
    assert openai_result["text"] == "ok"

    anthropic_result = next(r for r in results if r["provider"] == "anthropic")
    assert anthropic_result["error"] == "Invalid API key"
    assert "text" not in anthropic_result


def test_broadcast_unknown_provider_reported_inline(client):
    """broadcast reports an unknown provider target inline"""
    response = client.post(
        "/api/broadcast",
        json={"prompt": "hi", "targets": [{"provider": "nope", "model": "m"}]},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["provider"] == "nope"
    assert "error" in result


def test_broadcast_search_only_provider_rejected_inline(client):
    """broadcast rejects the search-only Tavily provider inline"""
    response = client.post(
        "/api/broadcast",
        json={"prompt": "hi", "targets": [{"provider": "tavily", "model": "x"}]},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["provider"] == "tavily"
    assert "error" in result


def test_broadcast_empty_prompt_returns_400(client):
    """broadcast rejects an empty prompt"""
    response = client.post(
        "/api/broadcast",
        json={"prompt": "   ", "targets": [{"provider": "openai", "model": "m"}]},
    )
    assert response.status_code == 400


def test_broadcast_empty_targets_returns_400(client):
    """broadcast rejects an empty target list"""
    response = client.post("/api/broadcast", json={"prompt": "hi", "targets": []})
    assert response.status_code == 400


def test_broadcast_too_many_targets_returns_400(client):
    """broadcast rejects more than 10 targets"""
    targets = [{"provider": "openai", "model": f"m{i}"} for i in range(11)]
    response = client.post("/api/broadcast", json={"prompt": "hi", "targets": targets})
    assert response.status_code == 400
    assert "10" in response.json()["detail"]


def test_broadcast_logs_counts_and_cost_never_bodies(client, monkeypatch, tmp_db):
    """broadcast logs counts/latency/cost only, never prompt or response bodies"""
    monkeypatch.setitem(
        PROVIDERS,
        "openai",
        StubProvider("openai", result=ok_result(text="secret response", prompt_tokens=1000, completion_tokens=500)),
    )
    seed_catalog(
        tmp_db,
        "openai",
        [{"id": "gpt-4o-mini", "context_window": None, "input_price_per_million": 5.0, "output_price_per_million": 15.0, "pricing_source": "api"}],
    )

    client.post(
        "/api/broadcast",
        json={"prompt": "say hi", "targets": [{"provider": "openai", "model": "gpt-4o-mini"}]},
    )

    rows = read_requests(tmp_db)
    assert len(rows) == 1
    row = rows[0]
    assert row["provider"] == "openai"
    assert row["model"] == "gpt-4o-mini"
    assert row["kind"] == "text"
    assert row["prompt_tokens"] == 1000
    assert row["completion_tokens"] == 500
    assert row["estimated_cost_usd"] == 0.0125

    columns = [c[1] for c in sqlite3.connect(tmp_db).execute("PRAGMA table_info(requests)")]
    assert not any("body" in c or "prompt_text" in c for c in columns)