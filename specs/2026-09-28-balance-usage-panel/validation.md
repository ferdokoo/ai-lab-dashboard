# Validation: Balance & Usage Panel

## Acceptance Criteria
- [ ] Every provider implements `balance()`, returning real data (OpenRouter, Tavily) or `None` (OpenAI, Anthropic, Gemini)
- [ ] `GET /api/{provider}/balance` returns a normalized payload for supported providers and an explicit "not available via API" state for the rest
- [ ] OpenRouter balance uses the management key and reports a clear error when only the inference key is configured
- [ ] Tavily balance surfaces per-key and account-plan usage
- [ ] Frontend balance panel shows real numbers where available and an honest "not available via API" message + billing link elsewhere (no placeholders or guesses)

## Test Coverage
- [ ] pytest: OpenRouter balance with management key (mocked response) returns normalized fields
- [ ] pytest: OpenRouter balance with no management key returns a clear "management key not configured" state
- [ ] pytest: Tavily `/usage` response normalizes per-key and account-plan usage
- [ ] pytest: OpenAI/Anthropic/Gemini `balance()` returns `None`
- [ ] pytest: route envelopes for both real-data and "not available" cases shape correctly
- [ ] Existing health/models/request tests still pass

## Manual Verification Steps
1. Set `OPENROUTER_MANAGEMENT_KEY` in `.env`, restart, and open the balance panel — OpenRouter credit/usage appear.
2. Remove `OPENROUTER_MANAGEMENT_KEY` (keep inference key), restart — OpenRouter shows "management key not configured" without erroring.
3. Set `TAVILY_API_KEY` and open the Tavily panel — per-key and plan usage render.
4. With OpenAI/Anthropic/Gemini keys set, open their panels — each shows "not available via API" plus a working link to the provider's billing page, and per-request token totals where applicable.
5. Confirm no provider shows a guessed or zeroed balance.

## Edge Cases
- Management key present but expired/invalid (HTTP error from OpenRouter)
- Tavily API returns unexpected/missing fields
- Provider with no key configured at all
- Missing billing metadata (link should degrade gracefully)
- Very large usage numbers / currency formatting

## Merge Checklist
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] No regressions in health checks, model catalog, or request runner