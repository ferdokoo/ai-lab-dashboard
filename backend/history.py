"""
History log queries.

Reads the ``requests`` table written by :mod:`backend.requestlog` so every past
call is browsable.  Only counts and metadata are exposed — the schema has no
prompt/response body column (mission principle 3).
"""
from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Any

import aiosqlite

from . import db

#: Fields returned by history queries, in display order.
_FIELDS = (
    "id",
    "timestamp",
    "provider",
    "model",
    "kind",
    "prompt_tokens",
    "completion_tokens",
    "estimated_cost_usd",
    "latency_ms",
)

_SELECT = ", ".join(_FIELDS)


def _build_where(
    provider: str | None,
    model: str | None,
    start: str | None,
    end: str | None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if model:
        clauses.append("model = ?")
        params.append(model)
    if start:
        clauses.append("substr(timestamp, 1, 10) >= ?")
        params.append(start)
    if end:
        clauses.append("substr(timestamp, 1, 10) <= ?")
        params.append(end)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


async def query_history(
    provider: str | None = None,
    model: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Return matching history rows (newest first) plus a total count."""
    await db.ensure_schema()
    where, params = _build_where(provider, model, start, end)

    async with aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row

        cursor = await conn.execute(f"SELECT COUNT(*) FROM requests {where}", params)
        total = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            f"SELECT {_SELECT} FROM requests {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        )
        rows = await cursor.fetchall()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def export_csv(
    provider: str | None = None,
    model: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> str:
    """Return the filtered history as CSV text (newest first)."""
    await db.ensure_schema()
    where, params = _build_where(provider, model, start, end)

    async with aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {_SELECT} FROM requests {where} ORDER BY id DESC", params
        )
        rows = await cursor.fetchall()

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_FIELDS)
    for row in rows:
        writer.writerow([row[field] for field in _FIELDS])
    return buffer.getvalue()


def _bucket(timestamp: str, group: str) -> str:
    """Reduce an ISO timestamp to a ``day`` or ``week`` bucket label."""
    if group == "week":
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%G-W%V")
    return timestamp[:10]


async def query_usage(
    group: str = "day",
    provider: str | None = None,
    model: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """Aggregate total tokens and estimated spend per day or week.

    Sums ``prompt_tokens + completion_tokens`` and ``estimated_cost_usd`` across
    matching rows, bucketed by timestamp.  ``None`` token/cost values simply
    contribute zero (Tavily searches count no tokens and little/no cost).
    Returns buckets in chronological order so the frontend can chart them.
    """
    await db.ensure_schema()
    where, params = _build_where(provider, model, start, end)

    async with aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT timestamp, prompt_tokens, completion_tokens, estimated_cost_usd "
            f"FROM requests {where} ORDER BY id ASC",
            params,
        )
        rows = await cursor.fetchall()

    buckets: dict[str, dict[str, float]] = {}
    for row in rows:
        key = _bucket(row["timestamp"], group)
        entry = buckets.setdefault(key, {"tokens": 0, "cost": 0.0})
        entry["tokens"] += (row["prompt_tokens"] or 0) + (row["completion_tokens"] or 0)
        if row["estimated_cost_usd"] is not None:
            entry["cost"] += row["estimated_cost_usd"]

    points = [
        {"bucket": key, "tokens": int(value["tokens"]), "cost": round(value["cost"], 8)}
        for key, value in sorted(buckets.items())
    ]
    return {"group": group, "points": points}