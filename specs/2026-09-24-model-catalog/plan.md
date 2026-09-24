# Plan: Model Catalog

## 1. Normalized models interface
- [ ] Confirm `backend/providers/base.py` declares `models()` returning a normalized list (id, context window, input $/1M, output $/1M)
- [ ] Implement `models()` in `openai.py` (list via `httpx` against `/models`, normalized)
- [ ] Implement `models()` in `anthropic.py` (list via `httpx` against `/models`, normalized)
- [ ] Implement `models()` in `gemini.py` (list via `httpx`, normalized)
- [ ] Implement `models()` in `openrouter.py` (list via `httpx` against `/models`, normalized)
- [ ] Implement `models()` in `tavily.py` where applicable (or return empty/not-applicable)

## 2. Pricing data
- [ ] Create `backend/pricing.py` with static pricing tables for OpenAI, Anthropic, Gemini (input/output $ per 1M tokens)
- [ ] Merge OpenRouter pricing from the live API response (it supplies price in its `/models` payload)
- [ ] Attach pricing to each normalized model entry; leave `None`/absent when unknown

## 3. API route + caching
- [ ] Add `GET /api/{provider}/models` route returning the normalized + priced list
- [ ] Cache catalog results in SQLite (`aiosqlite`) keyed by provider
- [ ] Support a refresh-on-demand flag (e.g. `?refresh=true`) to bypass cache and re-fetch
- [ ] Return consistent JSON shape across all providers

## 4. Frontend table
- [ ] Render one sortable table per provider (columns: model ID, context window, input $/1M, output $/1M)
- [ ] Add a refresh button per provider that hits the refresh flag and updates the table
- [ ] Handle empty/error states gracefully (e.g. provider without pricing, local providers in later phases)