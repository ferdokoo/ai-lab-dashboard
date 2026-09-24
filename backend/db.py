"""
Shared SQLite storage.

The dashboard keeps every persisted table in a single ``.db`` file.  This module
owns the schema (creating tables on demand) so both the model-catalog cache and
the request log write to the same database through the same ``aiosqlite``
pattern.
"""
from __future__ import annotations

import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dashboard.db"

_CATALOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog (
    provider TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
"""

_REQUESTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'text',
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    estimated_cost_usd REAL,
    latency_ms INTEGER
);
"""


async def ensure_schema(db_path: Path | None = None) -> None:
    """Create the database and any missing tables.

    ``db_path`` defaults to :data:`DB_PATH`; tests may pass a temporary path so
    they never touch the real on-disk database.
    """
    path = db_path if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.execute(_CATALOG_SCHEMA)
        await db.execute(_REQUESTS_SCHEMA)
        await db.commit()