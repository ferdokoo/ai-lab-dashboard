# Plan: Phase 2 — Health Checks

## 1. Abstract Provider Interface
- [x] Create `backend/providers/base.py` with abstract base class
- [x] Define abstract methods: `health()`, `models()`, `balance()`, `request()`
- [x] Document expected return shapes (status, latency, error message)

## 2. Provider Modules (one per provider)
- [x] `backend/providers/openai.py` — probe `GET https://api.openai.com/v1/models` (cheapest valid call)
- [x] `backend/providers/anthropic.py` — probe `POST https://api.anthropic.com/v1/messages` with minimal payload
- [x] `backend/providers/gemini.py` — probe `GET https://generativelanguage.googleapis.com/v1beta/models`
- [x] `backend/providers/openrouter.py` — probe `GET https://openrouter.ai/api/v1/models`
- [x] `backend/providers/tavily.py` — probe `POST https://api.tavily.com/search` with minimal payload
- [x] Each `health()` uses `httpx` (async), measures latency, returns `{status, latency_ms, error}`
- [x] Handle missing key in `.env`: return status `"missing_key"` without making a network call
- [x] Handle network timeout (set `httpx` timeout to ~5 s): return status `"timeout"`
- [x] Handle non-2xx response: return status `"error"` with HTTP status code

## 3. API Routes
- [x] Create `backend/routers/health.py` (or add to `main.py`) with `GET /api/{provider}/health`
- [x] Route validates provider name; returns 404 for unknown providers
- [x] Response schema: `{provider, status, latency_ms, error}` (error nullable)
- [x] Register router in `backend/main.py`

## 4. Frontend — Provider Cards
- [x] Add one card per provider to `frontend/index.html` (OpenAI, Anthropic, Gemini, OpenRouter, Tavily)
- [x] Each card has: provider name, "Check" button, status indicator (green/red/grey), latency badge
- [x] JS in `frontend/app.js`: `fetch('/api/{provider}/health')` on button click
- [x] Update card UI: green on `"ok"`, red on `"error"` / `"timeout"` / `"missing_key"`, grey while loading
- [x] Display response latency in ms next to indicator
- [x] Show a short error message beneath the indicator on failure

## 5. Manual End-to-End Verification
- [x] Start server with `uvicorn backend.main:app`
- [x] Test each provider card with a valid key — confirm green + latency
- [x] Remove a key from `.env`, retest — confirm red + "missing key" message
- [x] Test with an invalid key — confirm red + error message