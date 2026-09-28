"""
History-log routes.

* ``GET /api/history`` — filterable, paginated list of past requests (newest
  first), with provider/model/date-range filters.
* ``GET /api/history/export`` — the same filtered set as a downloadable CSV.

Both read the SQLite ``requests`` table, so no prompt/response bodies are ever
returned (they are never stored).
"""
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import Response

from .. import history

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history/usage")
async def get_history_usage(
    group: str = Query(default="day", pattern="^(day|week)$"),
    provider: str | None = None,
    model: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    """Return token and spend totals aggregated per day or week."""
    return await history.query_usage(
        group=group,
        provider=provider.strip() if provider else None,
        model=model.strip() if model else None,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
    )


@router.get("/history")
async def get_history(
    provider: str | None = None,
    model: str | None = None,
    start: date | None = None,
    end: date | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Return past requests, newest first, with optional filters and paging."""
    return await history.query_history(
        provider=provider.strip() if provider else None,
        model=model.strip() if model else None,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
        limit=limit,
        offset=offset,
    )


@router.get("/history/export")
async def export_history(
    provider: str | None = None,
    model: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> Response:
    """Return the filtered history as a downloadable CSV attachment."""
    csv_text = await history.export_csv(
        provider=provider.strip() if provider else None,
        model=model.strip() if model else None,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
    )
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="history.csv"'},
    )