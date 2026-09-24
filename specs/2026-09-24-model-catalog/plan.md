# Plan: Model Catalog

## 1. Normalized models interface
- [ ] Confirm `backend/providers/base.py` declares `models()` returning a normalized list (id, context window)
- [ ] Implement `models()` in `openai.py` (list via `httpx` against `/models`, normalized)
- [ ] Implement `models()` in `anthropic.py` (list via `httpx` against `/models`, normalized)
- [ ] Implement `models()` in `gemini.py` (list via `httpx`, normalized)
- [ ] Implement `models()` in `openrouter.py` (list via `httpx` against `/models`, normalized)
- [ ] Implement `models()` in `tavily.py` where applicable (or return empty/not-applicable)

## 2. Pricing data
- [ ] No static pricing tables: only use pricing a real source actually supplies
- [ ] Keep a separate list of available models per provider from its `models()` response
- [ ] Provider API returns prices (e.g. OpenRouter in its `/models` payload) → merge them into the normalized entries
- [ ] Provider API returns no prices → resolve prices for the top models via web search using the Tavily search tool
- [ ] Attach pricing to a model entry only when a real source returned it; leave `None`/absent otherwise

## 3. API route + caching
- [ ] Add `GET /api/{provider}/models` route returning the normalized + priced list
- [ ] Cache catalog results in SQLite (`aiosqlite`) keyed by provider
- [ ] Support a refresh-on-demand flag (e.g. `?refresh=true`) to bypass cache and re-fetch
- [ ] Return consistent JSON shape across all providers

## 4. Frontend table
- [ ] Render a provider dropdown; show models only for the selected provider
- [ ] Render one sortable table for the selected provider (columns: model ID, context window, input $/1M, output $/1M)
- [ ] Make the models table expandable/collapsible so the user can hide it to save space
- [ ] Add a refresh button that hits the refresh flag and updates the table for the selected provider
- [ ] Handle empty/error states gracefully (e.g. provider without pricing, local providers in later phases)