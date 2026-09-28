# Requirements: Cost Tools & Compare Mode

## Goal
Let a user know what a call will cost *before* running it, and fire one prompt at several provider/model pairs at once to compare outputs, latency, and cost side by side. The dashboard already caches per-model pricing (Phase 3) and can send a single prompt (Phase 4); this phase composes both into a cost calculator and a broadcast/compare mode.

## In Scope
- **Cost calculator**: input token counts, select provider + model, get a USD estimate from the **cached** pricing table.
- **Broadcast / compare mode**: one prompt sent to multiple provider+model pairs simultaneously; responses shown side by side with per-result latency and cost.
- `POST /api/broadcast` — parallel fan-out to selected models, collecting results per target.
- `GET /api/cost` (or `POST /api/cost/estimate`) — resolved estimate from cached catalog pricing.
- Frontend: model multi-select, side-by-side response cards with cost + latency badges, and an honest "unknown" state when a model has no cached price.

## Out of Scope
- Streaming / SSE on the compare or request runner (Phase 9).
- Storing prompt/response bodies in the request log for broadcast calls — remains disabled by default (mission principle 3).
- New pricing sources for the calculator — it reads the existing cached table only.
- Charts / aggregation (Phase 9).

## Key Decisions
- The cost calculator **reuses the existing pricing cache** (`backend/cache.py` + the `_estimate_cost` math in `backend/routers/request.py`); it does not perform new pricing lookups.
- The cost math is factored into a shared helper so the calculator and the request runner agree on the same formula.
- Broadcast fans out with `asyncio.gather(..., return_exceptions=True)` against the existing `request()` interface — no special-casing per provider, preserving mission principle 4 (extensible by design).
- A failing target (missing key, API error, offline local server) is reported inline per target; it does not abort sibling targets.
- Broadcast results are logged with counts/latency/cost only, mirroring Phase 4's privacy behavior.

## Context & Constraints
- Mission principle 2 (honest data): missing cached prices render as "unknown" with a pricing source hint — never a placeholder or zero.
- Mission principle 3 (local-first & private): everything stays local over SQLite; no prompt/response bodies logged.
- Mission principle 4 (extensible by design): broadcast calls the same `request()` interface every provider already implements.
- Tech stack: `aiosqlite` for the pricing cache, `httpx`-backed `request()`, vanilla `fetch` + no build step on the frontend.
- Windows + WSL2 must work without modification; keep the HTTP binding and DB path unchanged.