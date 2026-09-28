"""
Cost-calculator tests.

Covers ``GET /api/cost`` against the cached catalog pricing (redirected to a
temporary database via the ``tmp_db`` fixture).  Verifies token math, the honest
``null`` estimate for unknown/unpriced models, and input validation.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.main import app


def model_entry(
    model_id: str,
    input_price: float | None,
    output_price: float | None,
    source: str | None = "api",
) -> dict:
    return {
        "id": model_id,
        "context_window": None,
        "input_price_per_million": input_price,
        "output_price_per_million": output_price,
        "pricing_source": source,
    }


def seed_catalog(tmp_db, provider: str, models: list[dict]) -> None:
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


@pytest.fixture
def client(tmp_db):
    return TestClient(app)


def test_cost_returns_estimate_for_priced_model(client, tmp_db):
    """cost returns the correct estimate from cached pricing"""
    seed_catalog(
        tmp_db,
        "openai",
        [model_entry("gpt-4o-mini", input_price=5.0, output_price=15.0)],
    )

    response = client.get(
        "/api/cost",
        params={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estimated_cost_usd"] == 0.0125
    assert data["input_price_per_million"] == 5.0
    assert data["output_price_per_million"] == 15.0
    assert data["pricing_source"] == "api"


def test_cost_returns_null_for_unknown_model(client, tmp_db):
    """cost returns a null estimate for a model with no cached entry"""
    seed_catalog(
        tmp_db,
        "openai",
        [model_entry("gpt-4o-mini", input_price=5.0, output_price=15.0)],
    )

    response = client.get(
        "/api/cost",
        params={
            "provider": "openai",
            "model": "gpt-4o",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estimated_cost_usd"] is None
    assert data["input_price_per_million"] is None
    assert data["pricing_source"] is None


def test_cost_returns_null_for_unpriced_model(client, tmp_db):
    """cost returns a null estimate when the model has no prices at all"""
    seed_catalog(tmp_db, "ollama", [model_entry("llama3", input_price=None, output_price=None, source=None)])

    response = client.get(
        "/api/cost",
        params={
            "provider": "ollama",
            "model": "llama3",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estimated_cost_usd"] is None
    assert data["input_price_per_million"] is None
    assert data["output_price_per_million"] is None


def test_cost_unknown_provider_returns_404(client):
    """cost returns 404 for an unknown provider"""
    response = client.get(
        "/api/cost",
        params={"provider": "nope", "model": "m", "prompt_tokens": 1, "completion_tokens": 1},
    )
    assert response.status_code == 404


def test_cost_empty_model_returns_400(client):
    """cost rejects an empty model id"""
    response = client.get(
        "/api/cost",
        params={"provider": "openai", "model": "   ", "prompt_tokens": 1, "completion_tokens": 1},
    )
    assert response.status_code == 400


def test_cost_negative_tokens_returns_422(client):
    """cost rejects negative token counts"""
    response = client.get(
        "/api/cost",
        params={"provider": "openai", "model": "m", "prompt_tokens": -1, "completion_tokens": 1},
    )
    assert response.status_code == 422