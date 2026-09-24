# Validation: Model Catalog

## Acceptance Criteria
- [ ] `GET /api/{provider}/models` returns 200 with a normalised JSON list for OpenAI, Anthropic, Gemini, and OpenRouter
- [ ] Each entry contains model ID, context window, input $/1M, and output $/1M (pricing may be absent where unknown, but shape is consistent)
- [ ] OpenRouter entries carry pricing merged from the live API; OpenAI/Anthropic/Gemini entries carry pricing from `backend/pricing.py`
- [ ] Repeating a request without `?refresh=true` is served from cache; with `?refresh=true` it re-fetches and updates the cache
- [ ] The frontend renders a sortable table per provider with a working refresh button and sensible empty/error states

## Test Coverage
- Manual only (no automated test suite required for this phase)
- `pytest` not required; validation is via curl + browser per the chosen success criteria

## Manual Verification Steps
1. Start the server: `uvicorn backend.main:app` (no errors)
2. `curl "http://127.0.0.1:8000/api/openai/models"` → normalised list with static pricing
3. `curl "http://127.0.0.1:8000/api/anthropic/models"` and `.../gemini/models` → same shape
4. `curl "http://127.0.0.1:8000/api/openrouter/models"` → entries include live pricing
5. `curl "http://127.0.0.1:8000/api/openai/models?refresh=true"` → re-fetches (check timing/diff vs cached)
6. In the browser: each provider shows a sortable table; clicking a column header sorts; refresh button updates rows
7. Verify a provider without pricing in its catalog displays an honest blank/"—" rather than a fabricated number

## Edge Cases
- Provider API key missing or invalid → route should surface a clear error/status rather than a 500 stack trace
- Provider returns a model with no context window or no price → entry stays coherent, missing fields shown as absent
- Refresh while a provider is unreachable → cache should retain last-good data or show a clear error, not corrupt the store
- Local providers (Ollama/LM Studio) are not yet implemented → route for them should not exist/error cleanly this phase

## Merge Checklist
- [ ] All acceptance criteria met
- [ ] Manual verification steps pass
- [ ] No regressions to Phase 1 (scaffolding) or Phase 2 (health checks)
- [ ] `specs/roadmap.md` Phase 3 marked complete after merge