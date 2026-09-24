"""
Request log storage.

Every request — LLM completion or Tavily search — appends one row to the
``requests`` table.  Only counts and metadata are stored; prompt and response
bodies are intentionally never written (mission principle 3).
"""
from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite

from . import db

KIND_TEXT = "text"
KIND_SEARCH = "search"


async def log_request(
    provider: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    estimated_cost_usd: float | None,
    latency_ms: int | None,
    kind: str = KIND_TEXT,
) -> None:
    """Insert one request log row.

    ``kind`` is ``"text"`` for LLM providers and ``"search"`` for Tavily.
    Token/cost/latency fields may be ``None`` when a provider does not report
    them (e.g. Tavily token counts).
    """
    await db.ensure_schema()
    timestamp = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute(
            """
            INSERT INTO requests
                (timestamp, provider, model, kind, prompt_tokens,
                 completion_tokens, estimated_cost_usd, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                provider,
                model,
                kind,
                prompt_tokens,
                completion_tokens,
                estimated_cost_usd,
                latency_ms,
            ),
        )
        await conn.commit()