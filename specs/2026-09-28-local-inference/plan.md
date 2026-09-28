# Plan: Local Inference (Ollama + LM Studio)

## 1. Backend providers
- [x] Add `backend/providers/ollama.py` — `http://localhost:11434`, implements `health()`, `models()`, `request()`
- [x] Add `backend/providers/lmstudio.py` — `http://localhost:1234` (OpenAI-compatible), implements `health()`, `models()`, `request()`
- [x] Register both providers in the provider registry so they surface in health checks, model catalog, and request runner with no special-casing
- [x] Ensure `health()`/`models()`/`request()` return `None` or a clear "connection error" state when the local server is not running (no API key required)

## 2. Routing & response normalization
- [x] Confirm existing `/api/{provider}/health`, `/api/{provider}/models`, and `POST /api/{provider}/request` routes work for the new providers without routing changes
- [x] Normalize model list and request response shapes (context window, input/output $/1M as `None` where unknown, raw text, token counts, latency ms)

## 3. Frontend
- [x] Ollama and LM Studio cards appear alongside cloud providers
- [x] Cards grey out gracefully with a clear "not running" message when the local server is unreachable
- [x] Model picker and request runner work for local models once reachable

## 4. Tests
- [x] Add pytest coverage mocking the Ollama and LM Studio endpoints (health up/down, model list, request)
- [x] Cover connection-failure paths and graceful degradation