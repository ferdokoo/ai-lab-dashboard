"""
SQLite-backed cache for model catalog results.

Stores the normalized model list as JSON, keyed by provider, so repeated
``GET /api/{provider}/models`` requests are served without re-hitting the
provider API.  ``?refresh=true`` bypasses the cache and overwrites the entry.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from . import db


async def get_catalog(provider: str) -> list[dict[str, Any]] | None:
    """Return the cached model list for ``provider``, or ``None`` when absent."""
    await db.ensure_schema()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT data FROM catalog WHERE provider = ?", (provider,)
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    return json.loads(row[0])


async def set_catalog(provider: str, models: list[dict[str, Any]]) -> None:
    """Store (or overwrite) the cached model list for ``provider``."""
    await db.ensure_schema()
    payload = json.dumps(models)
    fetched_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute(
            """
            INSERT INTO catalog (provider, data, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                data = excluded.data,
                fetched_at = excluded.fetched_at
            """,
            (provider, payload, fetched_at),
        )
        await conn.commit()