# Requirements: Phase 2 — Health Checks

## Goal
Give developers instant, per-provider feedback on whether their API keys are valid and endpoints are reachable — directly from the dashboard, with no curl commands or separate provider consoles. Each provider shows a green or red indicator and a response time, letting the user confirm a new key is working in seconds.

## In Scope
- Abstract provider interface (`backend/providers/base.py`) defining `health()`, `models()`, `balance()`, `request()`
- `health()` implementation for all five cloud providers: OpenAI, Anthropic, Gemini, OpenRouter, Tavily
- `GET /api/{provider}/health` route for each provider
- Frontend: one card per provider with a "Check" button, green/red status indicator, and latency badge
- Error handling for: missing key, invalid/rejected key, network timeout, non-2xx responses

## Out of Scope
- `models()`, `balance()`, `request()` implementations (deferred to later phases)
- Local providers: Ollama and LM Studio (Phase 5)
- Request logging or SQLite writes
- Model catalog, request runner, cost tracking

## Key Decisions
- **Use `httpx` (async) for all health probes** — provider SDKs are not used here. This is consistent with the tech-stack constraint: SDKs are reserved for the request runner (Phase 4) where streaming and error shapes matter.
- **Cheapest available probe per provider** — prefer a read-only endpoint (model list, usage) over a write/inference call to avoid costs and side-effects.
- **Timeout set to ~5 seconds** — balances responsiveness against slow networks; returns `"timeout"` status if exceeded.
- **Missing key short-circuits** — no network call is made if the key is absent from `.env`; the frontend shows a distinct `"missing_key"` state.

## Context & Constraints

**From mission.md:**
- *Zero setup overhead* — the health check route must work the moment `uvicorn backend.main:app` starts; no migration, seed data, or extra config required.
- *Honest data* — status indicators must reflect the real probe result. Never show green if the key wasn't actually accepted by the provider.
- *Extensible by design* — `base.py` must define the full four-method interface now, even though only `health()` is implemented in this phase, so future phases can add methods without touching routing.

**From tech-stack.md:**
- Backend: FastAPI + uvicorn + httpx + python-dotenv
- Frontend: vanilla JS (`fetch`), no framework, no build step
- Secrets loaded from `.env` via `python-dotenv`; keys never hardcoded
- Compatible with Windows (native Python) and WSL2
