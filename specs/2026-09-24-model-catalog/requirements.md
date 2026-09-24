# Requirements: Model Catalog

## Goal
Let a developer browse all available models and their pricing from a single local screen without visiting provider docs. Each provider exposes `models()` in a normalised shape, pricing is attached (static tables where the API doesn't return it, live where it does), and results are cached in SQLite with a manual refresh.

## In Scope
- Normalized `models()` implementation for OpenAI, Anthropic, Gemini, OpenRouter (Tavily as applicable)
- No static pricing data: use provider-supplied prices when available, otherwise resolve top-model prices via the Tavily search tool
- `GET /api/{provider}/models` route with consistent JSON shape
- SQLite caching of catalog results with a refresh-on-demand flag
- Frontend: provider dropdown showing only the selected provider's models in a sortable, collapsible table (model ID, context window, input $/1M, output $/1M) with a refresh button

## Out of Scope
- Request runner (sending prompts) — that's Phase 4
- Local inference providers (Ollama / LM Studio) — Phase 5
- Balance / usage panel — Phase 6
- Cost calculator and compare/broadcast mode — Phase 8
- Streaming, rate-limit headers, dark theme, charts — Phase 9

## Key Decisions
- Keep a separate list of available models per provider from its `models()` response (no static model lists)
- Where the provider API returns price (e.g. OpenRouter), use it; where it doesn't (OpenAI, Anthropic, Gemini), resolve top-model prices via the Tavily search tool — no static pricing tables (mission.md "Honest data" principle)
- Pricing is normalized to USD per 1M tokens ($/1M) for input and output
- Unknown pricing is shown explicitly rather than guessed (`None`/empty, not a fake number)
- Catalog results are cached in SQLite with refresh-on-demand; no auto-refresh schedule in this phase
- The UI uses a provider dropdown (models shown only for the selected provider) and a collapsible table to save space

## Context & Constraints
- Python 3.11+, FastAPI + uvicorn backend; vanilla JS frontend with `fetch`, no build step (tech-stack.md)
- Use `httpx` for all probe calls (uniform async pattern; no provider SDKs for catalog listing)
- Use the Tavily search tool to look up top-model prices when the provider API doesn't supply them
- SQLite via `aiosqlite` for the catalog cache
- Keys stay in `.env`; server binds to `127.0.0.1` (mission.md principle 3)
- Providers implement the same small interface (`models()` among others) so routing/frontend need no special-casing per provider (mission.md principle 4)