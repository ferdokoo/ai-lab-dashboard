# Plan: Model Catalog

## 1. Normalized models interface
- [x] Confirm `backend/providers/base.py` declares `models()` returning a normalized list (id, context window)
- [x] Implement `models()` in `openai.py` (list via `httpx` against `/models`, normalized)
- [x] Implement `models()` in `anthropic.py` (list via `httpx` against `/models`, normalized)
- [x] Implement `models()` in `gemini.py` (list via `httpx`, normalized)
- [x] Implement `models()` in `openrouter.py` (list via `httpx` against `/models`, normalized)
- [x] Implement `models()` in `tavily.py` where applicable (or return empty/not-applicable)

## 2. Pricing data
- [x] No static pricing tables: only use pricing a real source actually supplies
- [x] Keep a separate list of available models per provider from its `models()` response
- [x] Provider API returns prices (e.g. OpenRouter in its `/models` payload) → merge them into the normalized entries
- [x] Provider API returns no prices → resolve prices for the top models via web search using the Tavily search tool
- [x] Attach pricing to a model entry only when a real source returned it; leave `None`/absent otherwise

## 3. API route + caching
- [x] Add `GET /api/{provider}/models` route returning the normalized + priced list
- [x] Cache catalog results in SQLite (`aiosqlite`) keyed by provider
- [x] Support a refresh-on-demand flag (e.g. `?refresh=true`) to bypass cache and re-fetch
- [x] Return consistent JSON shape across all providers

## 4. Frontend table
- [x] Render a provider dropdown; show models only for the selected provider
- [x] Render one sortable table for the selected provider (columns: model ID, context window, input $/1M, output $/1M)
- [x] Make the models table expandable/collapsible so the user can hide it to save space
- [x] Add a refresh button that hits the refresh flag and updates the table for the selected provider
- [x] Handle empty/error states gracefully (e.g. provider without pricing, local providers in later phases)