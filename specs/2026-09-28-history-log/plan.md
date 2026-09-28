# Plan: History Log

## 1. Backend — data access & API
- [x] Add a `backend/history.py` module exposing an async query function over the existing `requests` table (raw SQL via `aiosqlite`, matching the `backend/requestlog.py` + `backend/db.py` pattern).
- [x] Query support: filter by `provider`, `model`, `start`/`end` date range, and `limit`/`offset` pagination; include a `count`/`total` for pagination.
- [x] Add `backend/routers/history.py` with `GET /api/history`; register the router in `backend/main.py`.
- [x] Add `GET /api/history/export` (or `GET /api/history?format=csv`) returning the filtered rows as CSV with a `Content-Disposition` attachment header.
- [x] Return `None`-safe values for `prompt_tokens`, `completion_tokens`, `estimated_cost_usd`, and `latency_ms` (Tavily/search rows report these as `NULL`).

## 2. Backend — schema confirmation
- [x] Confirm the `requests` table already carries `id, timestamp, provider, model, prompt_tokens, completion_tokens, estimated_cost_usd, latency_ms` (it does — `backend/db.py`), so no migration is required; document the `kind` column in the query results.

## 3. Frontend — history table
- [x] Add a "History" panel in `frontend/index.html` / its script: provider + model filters, a date-range pair, and a table of past requests.
- [x] Sortable + filterable columns: timestamp, provider, model, prompt tokens, completion tokens, estimated cost, latency ms.
- [x] Add a "Export CSV" button that downloads the currently-filtered result set.

## 4. Tests
- [x] Add `backend/tests/test_history.py` covering the `GET /api/history` route with the `tmp_db` fixture: empty log, provider/model filter, date range, limit/offset, and NULL cost/latency rows.
- [x] Add tests for CSV export: correct headers, row count, and semantically-correct quoting/escaping.

## 5. Verification
- [x] Run the backend test suite; confirm no regressions in existing request/balance/model tests.
- [x] Manual smoke: run a couple of requests, then confirm they appear in the history table and export cleanly.