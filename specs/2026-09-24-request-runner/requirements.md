# Requirements: Request Runner

## Goal
Let a developer send a real prompt (or search query) to any configured provider from the dashboard and see the full response alongside token usage and latency — all without leaving localhost and without writing ad-hoc scripts. This closes the "confirm it works and run a test prompt" loop beyond health checks and the model catalog.

## In Scope
- `request(model, prompt, options)` for the four cloud LLM providers: OpenAI, Anthropic, Gemini, OpenRouter — implemented via their official SDKs.
- Tavily **search** requests as a distinct action (separate field for the query; not a "model prompt").
- `POST /api/{provider}/request` returning `{ text, prompt_tokens, completion_tokens, latency_ms }`.
- Writing every call to the SQLite request log (timestamp, provider, model, token counts, cost, latency) without storing prompt/response bodies.
- A dedicated frontend Requests page with provider + model pickers (models loaded live from `GET /api/{provider}/models`, cached and refreshable), a prompt textarea, and a response panel.

## Out of Scope
- Local inference providers (Ollama, LM Studio) — Phase 5.
- Balance/usage panel and honest "not available via API" messaging — Phase 6.
- History log browsing UI, filters, sorting, and CSV export — Phase 7.
- Cost calculator and broadcast/compare mode — Phase 8.
- Streaming (SSE) toggle, rate-limit header inspector, dark theme — Phase 9.
- Storing full prompt/response bodies (kept excluded per privacy principle unless explicitly opted in).

## Key Decisions
- **Logging first.** The SQLite `requests` table and `log_request()` helper are built before the `request` routes so nothing is ever left uncaptured during development.
- **Tavily is a separate request kind, not a model.** It carries a search query field rather than a model id; token counts are reported honestly (possibly `None`) rather than fabricated.
- **SDK-backed for request() only.** Per tech-stack, probes (`health`/`models`) stay on `httpx`; the request runner uses official SDKs where streaming/error shapes matter.
- **Separate frontend page for requests** rather than cramming it into the health-check screen.
- **Model list is live-or-cached.** The picker pulls from the existing model-catalog route and can be refreshed on demand.

## Context & Constraints
- **Honest data (mission principle 2):** report real token/latency numbers; don't invent Tavily token counts.
- **Local-first & private (mission principle 3):** requests only ever go over localhost; log stores counts, not bodies.
- **Extensible by design (mission principle 4):** all providers expose the same `request()` shape so no routing/frontend special-casing is needed for LLM providers; Tavily is the one deliberate exception as a search action.
- **Tech-stack SDKs:** `openai` (OpenAI + OpenRouter), `anthropic`, `google-genai` for Gemini.
- **SQLite via `aiosqlite`** matching the Phase 3 pattern; single `.db` file.
- **Windows native + WSL2 compatible** per mission success criteria.
```