# Plan: Request Runner

## 1. Request Log Storage (log-first foundation)
- [x] Create/confirm the SQLite `requests` table with schema: `id, timestamp, provider, model, prompt_tokens, completion_tokens, estimated_cost_usd, latency_ms`
- [x] Add a `kind` column (`text` for LLM providers, `search` for Tavily) alongside the above columns
- [x] Implement an async `log_request()` helper using `aiosqlite` so every call is writable before any route exists
- [x] Confirm the DB access pattern matches the existing Phase 3 SQLite usage (single `.db` file, async connection)

## 2. Provider `request()` Implementations
- [x] Add `request(model, prompt, options)` to `backend/providers/base.py` as a defined abstract (or documented) method alongside `health()` / `models()` / `balance()`
- [x] `openai.py` — implement `request()` via the `openai` SDK returning raw text + token usage + latency
- [x] `anthropic.py` — implement `request()` via the `anthropic` SDK
- [x] `gemini.py` — implement `request()` via the `google-genai` SDK
- [x] `openrouter.py` — implement `request()` via the `openai` SDK pointed at the OpenRouter-compatible endpoint
- [x] `tavily.py` — implement a search request (separate `search`-style entry point) returning result text; token/latency fields handled honestly (tokens may be `None`)

## 3. Request Endpoints
- [x] `POST /api/{provider}/request` — accepts `{ model, prompt, options }`; returns `{ text, prompt_tokens, completion_tokens, latency_ms }`
- [x] Add a Tavily search endpoint/route path (e.g. `POST /api/tavily/search`) capturing the search query as a separate field rather than a model prompt
- [x] Wire every successful (and failed) call into the request log; prompt/response bodies are **not** stored by default
- [x] Normalise provider-specific response shapes (text, usage, latency) into one payload contract

## 4. Frontend — Request Runner Page
- [x] Add a dedicated Requests page/route in the frontend navigation (separate from health cards and model catalog)
- [x] Provider picker (cloud providers + Tavily) and model picker populated live from `GET /api/{provider}/models` (cached, refreshable)
- [x] Prompt textarea (cached model list refresh button nearby)
- [x] Response panel showing output text plus prompt tokens, completion tokens, and latency ms
- [x] Copy and Clear buttons next to the token/latency metrics to copy the response text to the clipboard or reset the output
- [x] Loading and error states (bad key, timeout, provider unreachable) surfaced clearly

## 5. Tests
- [x] Write pytest tests for the `request` route and log-writing using mocked SDKs (per validation.md)