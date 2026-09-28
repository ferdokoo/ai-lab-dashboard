"""
Phase 9 (Polish) route tests.

Covers the newer endpoints and behaviour:

* ``GET /api/history/usage`` — token/spend aggregation per day or week.
* ``GET /api/keys`` — masked key listing (last four characters only).
* rate-limit headers surfaced in the ``POST /api/{provider}/request`` payload.
* ``POST /api/{provider}/request/stream`` — Server-Sent Events streaming.
"""
from __future__ import annotations

import asyncio
import sqlite3
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.config import settings
from backend.main import app
from backend.providers import PROVIDERS
from backend.providers.base import ProviderError, extract_rate_limits


@pytest.fixture
def client(tmp_db):
    return TestClient(app)


def seed(tmp_db, rows):
    """Create the schema and insert history rows for the usage endpoint."""
    asyncio.run(db.ensure_schema())
    conn = sqlite3.connect(tmp_db)
    try:
        conn.executemany(
            """
            INSERT INTO requests
                (timestamp, provider, model, kind, prompt_tokens,
                 completion_tokens, estimated_cost_usd, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["timestamp"],
                    row["provider"],
                    row["model"],
                    row.get("kind", "text"),
                    row.get("prompt_tokens"),
                    row.get("completion_tokens"),
                    row.get("estimated_cost_usd"),
                    row.get("latency_ms"),
                )
                for row in rows
            ],
        )
        conn.commit()
    finally:
        conn.close()


# --- Usage aggregation -------------------------------------------------------


def test_usage_empty_database(client):
    """usage returns an empty point list for a fresh database"""
    response = client.get("/api/history/usage")

    assert response.status_code == 200
    data = response.json()
    assert data["group"] == "day"
    assert data["points"] == []


def test_usage_daily_aggregation(client, tmp_db):
    """usage sums tokens and cost per day"""
    seed(
        tmp_db,
        [
            {
                "timestamp": "2026-09-28T10:00:00+00:00",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "estimated_cost_usd": 0.01,
            },
            {
                "timestamp": "2026-09-28T12:00:00+00:00",
                "provider": "anthropic",
                "model": "claude",
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "estimated_cost_usd": 0.02,
            },
            {
                "timestamp": "2026-09-29T09:00:00+00:00",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "prompt_tokens": 7,
                "completion_tokens": 3,
                "estimated_cost_usd": None,
            },
        ],
    )

    data = client.get("/api/history/usage?group=day").json()

    assert [p["bucket"] for p in data["points"]] == ["2026-09-28", "2026-09-29"]
    assert data["points"][0]["tokens"] == 45
    assert data["points"][0]["cost"] == 0.03
    assert data["points"][1]["tokens"] == 10
    assert data["points"][1]["cost"] == 0.0


def test_usage_weekly_aggregation(client, tmp_db):
    """usage buckets by ISO week"""
    seed(
        tmp_db,
        [
            {
                "timestamp": "2026-09-28T10:00:00+00:00",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "prompt_tokens": 5,
                "completion_tokens": 5,
                "estimated_cost_usd": 0.001,
            },
            {
                "timestamp": "2026-09-29T10:00:00+00:00",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "prompt_tokens": 5,
                "completion_tokens": 5,
                "estimated_cost_usd": 0.002,
            },
        ],
    )

    data = client.get("/api/history/usage?group=week").json()

    assert data["group"] == "week"
    assert len(data["points"]) == 1
    assert data["points"][0]["tokens"] == 20


def test_usage_invalid_group_rejected(client):
    """usage rejects an unknown grouping"""
    response = client.get("/api/history/usage", params={"group": "hour"})
    assert response.status_code == 422


# --- Masked keys -------------------------------------------------------------


def test_keys_are_masked(client, monkeypatch):
    """keys endpoint masks every key down to its last four characters"""
    monkeypatch.setattr(settings, "openai_api_key", "sk-abcdefghijk1234")
    monkeypatch.setattr(settings, "anthropic_api_key", None)

    data = client.get("/api/keys").json()

    by_provider = {entry["provider"]: entry for entry in data["keys"]}

    assert by_provider["openai"]["configured"] is True
    assert by_provider["openai"]["masked"] == "••••1234"
    assert "abcdefghijk1234" not in by_provider["openai"]["masked"]

    assert by_provider["anthropic"]["configured"] is False
    assert by_provider["anthropic"]["masked"] is None

    assert by_provider["ollama"]["configured"] is None
    assert by_provider["ollama"]["note"]


# --- Rate-limit headers ------------------------------------------------------


class RateLimitStub:
    """Provider stub that returns rate-limit headers in its request result."""

    name = "openai"

    async def request(self, model, prompt, options=None):
        return {
            "text": "ok",
            "prompt_tokens": 3,
            "completion_tokens": 2,
            "latency_ms": 10,
            "rate_limit": {
                "x-ratelimit-limit-requests": "60",
                "x-ratelimit-remaining-requests": "59",
            },
        }


def test_request_returns_rate_limit_headers(client, tmp_db, monkeypatch):
    """request route surfaces rate-limit headers when the provider returns them"""
    monkeypatch.setitem(PROVIDERS, "openai", RateLimitStub())

    data = client.post(
        "/api/openai/request", json={"model": "gpt-4o-mini", "prompt": "hi"}
    ).json()

    assert data["rate_limit"]["x-ratelimit-limit-requests"] == "60"
    assert data["rate_limit"]["x-ratelimit-remaining-requests"] == "59"


def test_extract_rate_limits_filters_and_ignores_unrelated():
    """extract_rate_limits keeps only x-ratelimit-* headers and returns None when absent"""

    class Headers:
        def items(self):
            return [
                ("x-ratelimit-remaining", "5"),
                ("content-type", "application/json"),
                ("X-Ratelimit-Limit", "10"),
            ]

    result = extract_rate_limits(Headers())
    assert result == {"x-ratelimit-remaining": "5", "X-Ratelimit-Limit": "10"}
    assert extract_rate_limits(None) is None


# --- Streaming ---------------------------------------------------------------


class StreamStub:
    """Provider stub that yields normalized stream events."""

    name = "openai"

    def __init__(self, error: ProviderError | None = None) -> None:
        self._error = error

    async def stream(self, model, prompt, options=None):
        if self._error is not None:
            raise self._error
        yield {"type": "delta", "content": "Hel"}
        yield {"type": "delta", "content": "lo"}
        yield {"type": "done", "prompt_tokens": 4, "completion_tokens": 2}


def test_stream_route_emits_sse(client, tmp_db, monkeypatch):
    """stream route emits deltas then a final done event over server-sent events"""
    monkeypatch.setitem(PROVIDERS, "openai", StreamStub())

    response = client.post(
        "/api/openai/request/stream", json={"model": "gpt-4o-mini", "prompt": "hi"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    body = response.text
    assert '"event": "delta"' in body
    assert '"content": "Hel"' in body
    assert '"content": "lo"' in body
    assert '"event": "done"' in body
    assert '"prompt_tokens": 4' in body


def test_stream_route_logs_request(client, tmp_db, monkeypatch):
    """stream route writes a request log row"""
    monkeypatch.setitem(PROVIDERS, "openai", StreamStub())

    client.post("/api/openai/request/stream", json={"model": "gpt-4o-mini", "prompt": "hi"})

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT provider, model, prompt_tokens, completion_tokens FROM requests"
    ).fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0]["provider"] == "openai"
    assert rows[0]["prompt_tokens"] == 4
    assert rows[0]["completion_tokens"] == 2


def test_stream_route_emits_error_event(client, tmp_db, monkeypatch):
    """stream route surfaces a provider error as an SSE error event"""
    monkeypatch.setitem(
        PROVIDERS, "openai", StreamStub(error=ProviderError("Invalid API key", 401))
    )

    response = client.post(
        "/api/openai/request/stream", json={"model": "gpt-4o-mini", "prompt": "hi"}
    )

    assert response.status_code == 200
    assert '"event": "error"' in response.text
    assert '"Invalid API key"' in response.text