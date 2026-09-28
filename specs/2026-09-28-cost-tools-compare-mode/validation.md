# Validation: Cost Tools & Compare Mode

## Acceptance Criteria
- [ ] `GET /api/cost` (or its estimate route) returns a correct USD estimate for a provider/model that has cached pricing, using the same math as the request runner.
- [ ] Requesting cost for a model with no cached price returns a `null` estimate plus a `pricing_source` hint, never a fabricated zero.
- [ ] `POST /api/broadcast` fans out to all selected targets concurrently and returns one entry per target (result or error), with per-target latency and estimated cost.
- [ ] A failing target (missing key / offline local server / API error) is isolated to its own `error` entry and does not prevent sibling targets from returning.
- [ ] Empty prompt or empty target list returns `400`.
- [ ] The frontend cost calculator produces the estimate from token inputs, and the compare panel renders side-by-side cards with cost + latency badges.
- [ ] No prompt/response bodies are written to the request log for broadcast calls; token counts, latency, and estimated cost are logged.

## Test Coverage
Add `backend/tests/test_cost.py` and `backend/tests/test_broadcast.py` using the existing fixtures:
- [ ] Cost route: cached-price model returns the expected estimate; unknown model / unpriced model returns `null`; token math matches input/output per-million prices.
- [ ] Broadcast: multi-target fan-out returns all result entries; a provider with a missing key (or a mocked `ProviderError`) yields an inline error entry while other targets succeed; empty prompt and empty targets return `400`.
- [ ] Broadcast logging: request-log rows contain counts/latency/cost only, with no prompt/response body (assert the log schema/fields).
- [ ] Existing suites (`test_request_runner`, `test_history`, `test_balance`, `test_local_providers`) still pass — no regressions.

## Manual Verification Steps
1. Start the app (`uvicorn backend.main:app`) and open the Cost calculator panel.
2. Select a provider/model with cached pricing and enter token counts; confirm the estimate matches the catalog's per-million prices.
3. Select a local (Ollama/LM Studio) model with no public pricing; confirm the panel shows an honest "unknown" state rather than a number.
4. Open the Compare panel, select three provider/model pairs (e.g. OpenAI + Anthropic + Gemini), enter one prompt, and run; confirm three cards render side by side with latency + cost.
5. Include a target with a missing/offline provider (leave LM Studio off); confirm its card shows an error while the others return results.
6. Check the History panel; confirm the broadcast transcribed one row per target with counts/cost/latency and no prompt/response body.

## Edge Cases
- One target missing a key or pointing at an offline local server — isolated error entry, siblings unaffected.
- A selected model has no cached pricing — cost badge shows "unknown"; calculator returns `null`.
- Empty prompt / empty target list / unknown provider — `400` or inline error without a crash.
- Duplicate provider+model pairs in the target list — decide and document dedup behavior (either dedupe or run each explicitly and label results).
- Concurrency: many targets at once — gather collects incomplete/failed coroutines without hanging the response.

## Merge Checklist
- [ ] All acceptance criteria met.
- [ ] Backend test suite passing (including new `test_cost.py` and `test_broadcast.py`).
- [ ] No regressions in existing tests.
- [ ] Broadcast confirms no prompt/response bodies are logged.
- [ ] CHANGELOG updated (per project convention).