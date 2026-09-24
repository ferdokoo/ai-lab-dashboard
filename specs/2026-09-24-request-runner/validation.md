# Validation: Request Runner

## Acceptance Criteria
- [ ] Every cloud provider's `request(model, prompt, options)` returns `{ text, prompt_tokens, completion_tokens, latency_ms }`.
- [ ] `POST /api/{provider}/request` succeeds for OpenAI, Anthropic, Gemini, and OpenRouter with valid keys.
- [ ] Tavily search request returns result text via its own route/field and does not fabricate token counts.
- [ ] Each successful call writes one row to the SQLite `requests` table with correct provider, model, token counts, cost, and latency.
- [ ] Request log stores no prompt/response bodies by default.
- [ ] Frontend Requests page lets the user pick a provider, pick a model from the (cached, refreshable) list, enter a prompt, run it, and see output + usage metrics.
- [ ] Errors (invalid key, provider timeout, unreachable host) surface as clear UI messages without crashing the server.

## Test Coverage
- [ ] `backend` pytest suite covers the `request` route and `log_request()` using mocked provider SDKs (no live network calls).
- [ ] Tests assert the normalised payload shape (text, token counts, latency) for at least one OpenAI-compatible and one non-OpenAI provider.
- [ ] Tests assert a request row is written to SQLite on success and that no body text is persisted.
- [ ] Tests assert Tavily search results are logged distinctly (kind = `search`) with honest `None` token handling.
- [ ] Existing Phase 1–3 tests still pass (no regressions).

## Manual Verification Steps
1. Start with `uvicorn backend.main:app` and confirm it boots with no errors.
2. Open the Requests page; select **OpenAI**, pick a model from the dropdown, enter a prompt, click run.
3. Confirm the response shows output text, `prompt_tokens`, `completion_tokens`, and `latency_ms`.
4. Repeat for Anthropic, Gemini, and OpenRouter.
5. Switch to Tavily, enter a search query, run it, and confirm result text appears.
6. Inspect the SQLite DB and confirm each call produced exactly one log row with no stored prompt/response body.
7. Run with an intentionally invalid key and confirm a clear error message appears in the UI.

## Edge Cases
- Invalid or expired API key on each provider → clear error, request still logged with latency.
- Provider timeout / unreachable endpoint → graceful failure without server crash.
- Empty prompt → validation error (or no-op) surfaced to the user.
- Model id not in the cached list (e.g. refreshed list is stale) → request still proxied to provider and provider error surfaced.
- Tavily search returning tokens as `None` → UI renders "—" honestly, never `0`.
- Long or multi-line prompts → handled and never written to the log body.

## Merge Checklist
- [ ] All acceptance criteria met
- [ ] `pytest` suite passing (including new request tests and no Phase 1–3 regressions)
- [ ] Manual verification completed across all five providers plus Tavily
- [ ] Request log confirmed to omit prompt/response bodies by default
- [ ] No secrets or keys committed
```