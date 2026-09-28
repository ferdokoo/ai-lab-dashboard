# Plan: Cost Tools & Compare Mode

## 1. Backend — cost calculator
- [x] Add a `backend/cost.py` module exposing a shared `estimate_cost(provider, model, prompt_tokens, completion_tokens)` helper that reads the cached catalog pricing (reuse `backend/cache.py` `get_catalog()`), matching the `_estimate_cost` logic already in `backend/routers/request.py`.
- [x] Add `backend/routers/cost.py` with `GET /api/cost` (or `POST /api/cost/estimate`) accepting `provider`, `model`, `prompt_tokens`, `completion_tokens`, returning the USD estimate plus the per-million input/output prices used.
- [x] Return an honest "price unknown" shape (`null` estimate + `pricing_source`) when the model has no cached prices, rather than fabricating a zero.
- [x] Register the router in `backend/main.py`.

## 2. Backend — broadcast / compare
- [x] Add `POST /api/broadcast` accepting a single `prompt`, a shared `options` dict, and a list of `targets` (each `{provider, model}`).
- [x] Fan out to `PROVIDERS[provider].request(model, prompt, options)` concurrently via `asyncio.gather(..., return_exceptions=True)`.
- [x] Return one result per target: `{provider, model, text, prompt_tokens, completion_tokens, latency_ms, estimated_cost_usd}` — and for failed targets a per-target `{provider, model, error}` entry so one failure never blocks the others.
- [x] Write a request-log row per successful (and per failed) target via `backend/requestlog.py`, storing counts/latency/cost only — never prompt/response bodies (mission principle 3).
- [x] Guard: empty prompt or empty target list returns `400`; unknown provider/model in a target is reported inline rather than aborting the request.

## 3. Frontend — cost calculator
- [x] Add a "Cost calculator" panel in `frontend/index.html` / its script: provider + model picker (reusing catalog data), prompt/completion token inputs, and a computed USD estimate readout.
- [x] Show the underlying input/output per-million prices and pricing source; render "unknown" honestly when pricing is unavailable.
- [x] When the user selects a model with no cached price, surface a "refresh pricing" hint rather than a bogus number.

## 4. Frontend — compare mode
- [x] Add a "Compare" panel: model multi-select (provider + model pairs), a shared prompt textarea, and a "Run comparison" button.
- [x] Render one card per target showing output text, latency badge, token counts, and estimated-cost badge side by side.
- [x] Failed targets render a clear error card; re-running preserves the selected targets.

## 5. Tests
- [x] Add `backend/tests/test_cost.py` covering the cost route: cached price present, unknown model/price `null` estimate, and token math correctness against the pricing cache.
- [x] Add `backend/tests/test_broadcast.py` covering `POST /api/broadcast`: multi-target fan-out returns all results, a failing provider/missing-key target is isolated to its own error entry, empty prompt/targets return `400`, and no prompt/response bodies are written to the request log.

## 6. Verification
- [x] Run the backend test suite; confirm no regressions in existing request/history/balance/model tests.
- [x] Manual smoke: estimate a known model's cost, then run a one-prompt / three-model comparison and confirm side-by-side latency + cost render correctly.