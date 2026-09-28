"""
History-log tests.

Covers ``GET /api/history`` and the CSV export against the real SQLite schema
(redirected to a temporary file via the ``tmp_db`` fixture).  Verifies filtering,
pagination, NULL serialization, and CSV escaping.
"""
from __future__ import annotations

import asyncio
import csv
import io
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.main import app


def seed(tmp_db, rows):
    """Create the schema and insert the given history rows."""
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


def row(**overrides):
    base = {
        "timestamp": "2026-09-28T12:00:00+00:00",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt_tokens": 12,
        "completion_tokens": 7,
        "estimated_cost_usd": 0.000042,
        "latency_ms": 134,
    }
    base.update(overrides)
    return base


@pytest.fixture
def client(tmp_db):
    return TestClient(app)


def test_history_empty_returns_empty(client):
    """history returns empty list and zero total for a fresh database"""
    response = client.get("/api/history")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_history_returns_rows_newest_first(client, tmp_db):
    """history returns rows ordered newest first"""
    seed(
        tmp_db,
        [
            row(timestamp="2026-09-27T10:00:00+00:00", provider="anthropic", model="claude"),
            row(timestamp="2026-09-28T12:00:00+00:00", provider="openai", model="gpt-4o-mini"),
        ],
    )

    response = client.get("/api/history")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert [item["provider"] for item in data["items"]] == ["openai", "anthropic"]
    assert data["items"][0]["model"] == "gpt-4o-mini"
    assert data["items"][0]["prompt_tokens"] == 12
    assert data["items"][0]["estimated_cost_usd"] == 0.000042


def test_history_provider_filter(client, tmp_db):
    """history filters by provider"""
    seed(
        tmp_db,
        [
            row(provider="openai", model="gpt-4o-mini"),
            row(provider="anthropic", model="claude"),
        ],
    )

    response = client.get("/api/history", params={"provider": "anthropic"})

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["provider"] == "anthropic"


def test_history_model_filter(client, tmp_db):
    """history filters by exact model"""
    seed(
        tmp_db,
        [
            row(provider="openai", model="gpt-4o-mini"),
            row(provider="openai", model="gpt-4o"),
        ],
    )

    response = client.get("/api/history", params={"model": "gpt-4o"})

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["model"] == "gpt-4o"


def test_history_date_range_filter(client, tmp_db):
    """history filters by inclusive date range"""
    seed(
        tmp_db,
        [
            row(timestamp="2026-09-26T10:00:00+00:00", provider="gemini", model="gemini-pro"),
            row(timestamp="2026-09-28T10:00:00+00:00", provider="openai", model="gpt-4o-mini"),
            row(timestamp="2026-09-30T10:00:00+00:00", provider="anthropic", model="claude"),
        ],
    )

    response = client.get(
        "/api/history", params={"start": "2026-09-28", "end": "2026-09-28"}
    )

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["provider"] == "openai"


def test_history_pagination(client, tmp_db):
    """history paginates via limit/offset and reports the total"""
    seed(tmp_db, [row(model=f"model-{i}", timestamp=f"2026-09-28T{i:02d}:00:00+00:00") for i in range(5)])

    page = client.get("/api/history", params={"limit": 2, "offset": 2}).json()

    assert page["total"] == 5
    assert page["limit"] == 2
    assert page["offset"] == 2
    assert len(page["items"]) == 2


def test_history_null_fields_serialize_as_null(client, tmp_db):
    """history serializes missing token/cost/latency as null"""
    seed(
        tmp_db,
        [
            row(
                provider="tavily",
                model="",
                kind="search",
                prompt_tokens=None,
                completion_tokens=None,
                estimated_cost_usd=None,
                latency_ms=None,
            )
        ],
    )

    response = client.get("/api/history")

    data = response.json()
    item = data["items"][0]
    assert item["prompt_tokens"] is None
    assert item["completion_tokens"] is None
    assert item["estimated_cost_usd"] is None
    assert item["latency_ms"] is None


def test_history_invalid_date_returns_422(client):
    """history rejects a malformed date range"""
    response = client.get("/api/history", params={"start": "not-a-date"})
    assert response.status_code == 422


def test_history_limit_out_of_range_returns_422(client):
    """history rejects out-of-range limit"""
    response = client.get("/api/history", params={"limit": 0})
    assert response.status_code == 422


def test_history_unknown_provider_empty(client, tmp_db):
    """history returns an empty result for an unmatched provider filter"""
    seed(tmp_db, [row(provider="openai", model="gpt-4o-mini")])

    response = client.get("/api/history", params={"provider": "nope"})

    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_history_export_csv(client, tmp_db):
    """CSV export returns a valid attachment matching the filtered rows"""
    seed(
        tmp_db,
        [
            row(provider="openai", model="gpt-4o-mini"),
            row(provider="anthropic", model="claude"),
        ],
    )

    response = client.get("/api/history/export", params={"provider": "openai"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    parsed = list(csv.reader(io.StringIO(response.text)))
    header, data_row = parsed[0], parsed[1]
    assert header[0] == "id"
    assert header[2] == "provider"
    assert data_row[header.index("provider")] == "openai"
    assert data_row[header.index("model")] == "gpt-4o-mini"


def test_history_export_csv_escaping(client, tmp_db):
    """CSV export escapes commas and quotes in field values"""
    tricky = 'gpt,b "mini"'
    seed(tmp_db, [row(provider="openai", model=tricky)])

    response = client.get("/api/history/export")

    parsed = list(csv.reader(io.StringIO(response.text)))
    header = parsed[0]
    data_row = parsed[1]
    assert data_row[header.index("model")] == tricky