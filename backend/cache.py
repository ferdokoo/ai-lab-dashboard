"""
SQLite-backed cache for model catalog results.

Stores the normalized model list as JSON, keyed by provider, so repeated
``GET /api/{provider}/models`` requests are served without re-hitting the
provider API.  ``?refresh=true`` bypasses the cache and overwrites the entry.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "catalog.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog (
    provider TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
"""


async def get_catalog(provider: str) -> list[dict[str, Any]] | None:
    """Return the cached model list for ``provider``, or ``None`` when absent."""
    await _ensure_schema()
    async with aiosqlite.connect(_DB_PATH) as db:
        cursor = await db.execute(
            "SELECT data FROM catalog WHERE provider = ?", (provider,)
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    return json.loads(row[0])


async def set_catalog(provider: str, models: list[dict[str, Any]]) -> None:
    """Store (or overwrite) the cached model list for ``provider``."""
    await _ensure_schema()
    payload = json.dumps(models)
    fetched_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO catalog (provider, data, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                data = excluded.data,
                fetched_at = excluded.fetched_at
            """,
            (provider, payload, fetched_at),
        )
        await db.commit()


async def _ensure_schema() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(_SCHEMA)
        await db.commit()