# Requirements: History Log

## Goal
Make every past test call browsable so token usage and estimated spend are visible over time. The dashboard already writes one row per request to the SQLite `requests` table (Phase 4); this phase exposes that data through a filterable API, a sortable frontend table, and a CSV export.

## In Scope
- `GET /api/history` with filter params: `provider`, `model`, date range, and `limit`/`offset` pagination.
- Filterable + sortable frontend table showing timestamp, provider, model, prompt tokens, completion tokens, estimated cost, and latency.
- CSV export of the currently-filtered results.
- Honest rendering of `NULL` token/cost/latency fields (search rows and providers that don't report them).

## Out of Scope
- Charts / usage-over-time aggregation (Phase 9).
- Replay, broadcast, and side-by-side compare mode (Phase 8).
- Cost calculator (Phase 8).
- Storing full prompt/response bodies — remains disabled by default (mission principle 3).

## Key Decisions
- Reuse the existing `requests` table and the `aiosqlite` + raw-SQL pattern in `backend/requestlog.py` / `backend/db.py`; no schema migration needed since `estimated_cost_usd` is already present.
- Add a dedicated `backend/history.py` module for queries and a `backend/routers/history.py` router, registered in `backend/main.py`.
- CSV export is a separate endpoint (or format param) with an attachment `Content-Disposition` header so the browser downloads rather than renders it.

## Context & Constraints
- Mission principle 2 (honest data): show `NULL` counts/costs explicitly rather than inventing zeros; sort and filter must handle `NULL`.
- Mission principle 3 (local-first & private): reads stay local over SQLite; no new external dependencies.
- Tech stack: vanilla `fetch` frontend, no build step; SQLite via `aiosqlite`; no `pandas`/CSV library — generate CSV with the stdlib `csv` module over the in-memory rows.
- Windows + WSL2 must work without modification; keep the DB path and HTTP binding unchanged.