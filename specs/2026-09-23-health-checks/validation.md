# Validation: Phase 2 — Health Checks

## Acceptance Criteria
- [ ] `GET /api/{provider}/health` returns valid JSON for all five providers: `openai`, `anthropic`, `gemini`, `openrouter`, `tavily`
- [ ] Response always includes `provider`, `status`, `latency_ms`, and `error` (nullable) fields
- [ ] Valid key → `status: "ok"`, `latency_ms` populated, `error: null`
- [ ] Missing key in `.env` → `status: "missing_key"`, no network call made, `latency_ms: null`
- [ ] Invalid/rejected key → `status: "error"`, HTTP provider status code surfaced in `error`
- [ ] Unreachable endpoint (timeout) → `status: "timeout"`, no unhandled exception
- [ ] Frontend: green indicator displayed for `"ok"` state
- [ ] Frontend: red indicator displayed for `"error"`, `"timeout"`, and `"missing_key"` states
- [ ] Frontend: latency in ms shown alongside indicator on success
- [ ] Frontend: short human-readable error message shown beneath indicator on failure
- [ ] Unknown provider name in route returns HTTP 404

## Test Coverage
- Unit tests for each provider's `health()` method using `httpx`-mock or `respx`:
  - Mock 200 response → assert `status == "ok"` and `latency_ms > 0`
  - Mock 401/403 response → assert `status == "error"`
  - Mock timeout → assert `status == "timeout"`
  - No key in environment → assert `status == "missing_key"` without any HTTP call
- Integration test (optional, requires real keys): call each live endpoint and assert `status == "ok"`

## Manual Verification Steps
1. Copy `.env.example` to `.env` and fill in all five real API keys.
2. Run `uvicorn backend.main:app` — confirm no startup errors.
3. Open `http://127.0.0.1:8000` in a browser.
4. Click "Check" on each provider card — all five should turn green with a latency reading.
5. Remove one key from `.env` (or set it to an empty string), restart the server, recheck that card — should turn red with a "missing key" message.
6. Set a key to a known-bad value (e.g., `sk-invalid`), restart, recheck — should turn red with an error message from the provider.
7. `curl http://127.0.0.1:8000/api/unknown/health` — should return HTTP 404.

## Edge Cases
| Case | Expected behaviour |
|---|---|
| Key present in `.env` but empty string | Treated as missing; `status: "missing_key"` |
| Provider returns unexpected JSON shape | Handled gracefully; `status: "error"` with a message |
| Network timeout (>5 s) | `status: "timeout"`; no unhandled exception; UI shows red |
| Provider temporarily returns 5xx | `status: "error"` with HTTP status in error field |
| Invalid key format (too short, wrong prefix) | Network call made; provider rejects it; `status: "error"` |

## Merge Checklist
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing for all five providers (all four mock scenarios)
- [ ] `GET /api/{provider}/health` manually verified for each live provider
- [ ] Missing key and invalid key edge cases manually confirmed in the UI
- [ ] No unhandled exceptions under any tested error condition
- [ ] `backend/providers/base.py` defines all four interface methods (even if only `health()` is implemented)
- [ ] No provider SDK imports in any health probe code
- [ ] Server still starts cleanly with `uvicorn backend.main:app` on Windows and WSL2
