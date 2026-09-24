# Plan: Request Runner

## 1. Request Log Storage (log-first foundation)
- [ ] Create/confirm the SQLite `requests` table with schema: `id, timestamp, provider, model, prompt_tokens, completion_tokens, estimated_cost_usd, latency_ms`
- [ ] Add a `kind` column (`text` for LLM providers, `search` for Tavily) alongside the above columns
- [ ] Implement an async `log_request()` helper using `aiosqlite` so every call is writable before any route exists
- [ ] Confirm the DB access pattern matches the existing Phase 3 SQLite usage (single `.db` file, async connection)

## 2. Provider `request()` Implementations
- [ ] Add `request(model, prompt, options)` to `backend/providers/base.py` as a defined abstract (or documented) method alongside `health()` / `models()` / `balance()`
- [ ] `openai.py` — implement `request()` via the `openai` SDK returning raw text + token usage + latency
- [ ] `anthropic.py` — implement `request()` via the `anthropic` SDK
- [ ] `gemini.py` — implement `request()` via the `google-genai` SDK
- [ ] `openrouter.py` — implement `request()` via the `openai` SDK pointed at the OpenRouter-compatible endpoint
- [ ] `tavily.py` — implement a search request (separate `search`-style entry point) returning result text; token/latency fields handled honestly (tokens may be `None`)

## 3. Request Endpoints
- [ ] `POST /api/{provider}/request` — accepts `{ model, prompt, options }`; returns `{ text, prompt_tokens, completion_tokens, latency_ms }`
- [ ] Add a Tavily search endpoint/route path (e.g. `POST /api/tavily/search`) capturing the search query as a separate field rather than a model prompt
- [ ] Wire every successful (and failed) call into the request log; prompt/response bodies are **not** stored by default
- [ ] Normalise provider-specific response shapes (text, usage, latency) into one payload contract

## 4. Frontend — Request Runner Page
- [ ] Add a dedicated Requests page/route in the frontend navigation (separate from health cards and model catalog)
- [ ] Provider picker (cloud providers + Tavily) and model picker populated live from `GET /api/{provider}/models` (cached, refreshable)
- [ ] Prompt textarea (cached model list refresh button nearby)
- [ ] Response panel showing output text plus prompt tokens, completion tokens, and latency ms
- [ ] Loading and error states (bad key, timeout, provider unreachable) surfaced clearly

## 5. Tests
- [ ] Write pytest tests for the `request` route and log-writing using mocked SDKs (per validation.md)
```