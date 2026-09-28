# Requirements: Balance & Usage Panel

## Goal
Show real credit/balance and usage numbers for the providers whose APIs actually expose them, and be honest where they don't. A developer can see at a glance how much credit is left (OpenRouter, Tavily) or, for providers without a balance API, see per-request token totals and a direct link to the provider's billing page — never a placeholder or a guess.

## In Scope
- `balance()` implemented on every provider, returning real data or `None`
- OpenRouter: real credit/usage via the management key (`OPENROUTER_MANAGEMENT_KEY`, distinct from the inference key)
- Tavily: per-key and account-plan usage via `GET /usage`
- OpenAI / Anthropic / Gemini: `balance()` returns `None`; UI falls back to per-request token totals + billing link
- Ollama / LM Studio: `balance()` returns `None`; excluded from the balance panel (no remote balance or billing to report)
- `GET /api/{provider}/balance` route returning a normalized shape for real-data providers and an explicit "not available via API" state for the rest
- Frontend balance panel per cloud provider with an honest "not available via API" message and billing links for unsupported providers

## Out of Scope
- Cost calculator / per-call cost estimates (Phase 8)
- Chart.js usage-over-time panels (Phase 9)
- History log UI (Phase 7)
- Any static/guessed balance values — no placeholders
- Local providers (Ollama, LM Studio) in the balance panel — nothing to report

## Key Decisions
- `balance()` returns a **normalized dict plus raw payload**: a stable normalized shape (e.g. credits/usage/plan fields) for the panel, plus an optional `raw` field carrying the provider's original response for provider-specific details
- OpenRouter balance requires `OPENROUTER_MANAGEMENT_KEY`; if only the inference key is present, balance reports "management key not configured" explicitly
- Unsupported providers return `None` rather than an empty/zeroed object, so the UI can cleanly distinguish "no API" from "zero balance"
- Billing links are static, documented provider URLs surfaced in the UI (no scraping or guessing)
- Local providers (Ollama, LM Studio) are omitted from the balance panel entirely, since they have no remote balance or billing page

## Context & Constraints
- Mission principle 2 (**Honest data**): display real numbers where the API surfaces them; where it doesn't, say so explicitly and link to the provider's billing page
- Mission principle 4 (**Extensible by design**): `balance()` is already part of the shared interface in `backend/providers/base.py` — no router/frontend special-casing
- Tech stack: use `httpx` for probe calls (SDKs reserved for request runner); vanilla JS frontend, no build step
- `.env.example` already documents `OPENROUTER_MANAGEMENT_KEY`

(End of file - total 41 lines)