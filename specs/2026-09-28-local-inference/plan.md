# Plan: Local Inference (Ollama + LM Studio)

## 1. Backend providers
- [ ] Add `backend/providers/ollama.py` — `http://localhost:11434`, implements `health()`, `models()`, `request()`
- [ ] Add `backend/providers/lmstudio.py` — `http://localhost:1234` (OpenAI-compatible), implements `health()`, `models()`, `request()`
- [ ] Register both providers in the provider registry so they surface in health checks, model catalog, and request runner with no special-casing
- [ ] Ensure `health()`/`models()`/`request()` return `None` or a clear "connection error" state when the local server is not running (no API key required)

## 2. Routing & response normalization
- [ ] Confirm existing `/api/{provider}/health`, `/api/{provider}/models`, and `POST /api/{provider}/request` routes work for the new providers without routing changes
- [ ] Normalize model list and request response shapes (context window, input/output $/1M as `None` where unknown, raw text, token counts, latency ms)

## 3. Frontend
- [ ] Ollama and LM Studio cards appear alongside cloud providers
- [ ] Cards grey out gracefully with a clear "not running" message when the local server is unreachable
- [ ] Model picker and request runner work for local models once reachable

## 4. Tests
- [ ] Add pytest coverage mocking the Ollama and LM Studio endpoints (health up/down, model list, request)
- [ ] Cover connection-failure paths and graceful degradation