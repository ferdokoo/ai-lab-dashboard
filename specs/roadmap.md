# Roadmap: Local AI Lab Dashboard

## Phase 1 — Scaffolding ✓ _complete_
_Goal:_ Prove the full loop works end-to-end so every subsequent phase has a reliable foundation to build on.
- Repo layout: `backend/`, `frontend/`, `specs/`
- Python venv + `requirements.txt`
- `.env.example` with all expected key names
- `backend/config.py` loading `.env` via `python-dotenv`
- FastAPI app (`backend/main.py`) serving the static frontend page
- One placeholder provider module to validate the interface shape
- `uvicorn backend.main:app` starts with no errors

## Phase 2 — Health Checks ✓ _complete_
_Goal:_ Tell you instantly which keys are valid and which endpoints are reachable.
- `backend/providers/base.py` — abstract interface: `health()`, `models()`, `balance()`, `request()`
- Provider modules: `openai.py`, `anthropic.py`, `gemini.py`, `openrouter.py`, `tavily.py`
- Each implements `health()` via the cheapest available probe call
- `GET /api/{provider}/health` route returning status + latency
- Frontend: one card per provider, button triggers health check, green/red indicator + response time

## Phase 3 — Model Catalog ✓ _complete_
_Goal:_ Browse all available models and their pricing from one place without visiting provider docs.
- Each provider implements `models()` returning a normalised list
- `backend/pricing.py` — resolves top-model prices via the Tavily search tool for providers that don't return price in the API (OpenAI, Anthropic, Gemini); no static tables
- OpenRouter pricing merged from live API response
- `GET /api/{provider}/models` route; results cached in SQLite with a refresh-on-demand button
- Frontend: provider dropdown + collapsible sortable table (model ID, context window, input $/1M, output $/1M)

## Phase 4 — Request Runner _complete_
_Goal:_ Send a real prompt to any cloud model and see the full response, latency, and token usage.
- Each cloud provider implements `request(model, prompt, options)` using its official SDK
- `POST /api/{provider}/request` route
- Response payload includes: raw text, prompt tokens, completion tokens, latency ms
- Frontend: provider + model picker, prompt textarea, response panel showing output + usage metrics
- Every call written to the SQLite request log (no prompt/response body stored by default)

## Phase 5 — Local Inference (Ollama + LM Studio) _complete_
_Goal:_ Treat locally-running models as first-class providers alongside cloud APIs.
- `backend/providers/ollama.py` — probes `localhost:11434`; implements `health()`, `models()`, `request()`
- `backend/providers/lmstudio.py` — probes `localhost:1234` (OpenAI-compatible API); implements the same interface
- Both providers surface in health checks, model catalog, and request runner without special-casing
- Frontend: Ollama and LM Studio cards appear alongside cloud providers; greyed out gracefully when the local server isn't running
- No API key required; connection failure is surfaced clearly

## Phase 6 — Balance & Usage Panel _complete_
_Goal:_ Show real credit/balance numbers where the API supports it; be honest where it doesn't.
- Each provider implements `balance()` — returns real data or `None`
- OpenRouter: requires management key (separate from inference key); documented in `.env.example`
- Tavily: `GET /usage` — returns per-key and account plan usage
- OpenAI / Anthropic / Gemini: `balance()` returns `None`; UI shows per-request token totals instead and links to provider billing page
- Frontend: balance panel per provider; honest "not available via API" message with billing link for unsupported providers

## Phase 7 — History Log _complete_
_Goal:_ Make every past test call browsable so patterns and costs are visible over time.
- SQLite schema: `requests(id, timestamp, provider, model, prompt_tokens, completion_tokens, estimated_cost_usd, latency_ms)`
- `GET /api/history` with filter params: provider, model, date range, limit/offset
- Frontend: filterable + sortable table of past requests; cost and token columns
- CSV export of filtered results

## Phase 8 — Cost Tools & Compare Mode _complete_
_Goal:_ Estimate costs before running and compare model outputs side by side.
- **Cost calculator**: input token counts, select provider + model, get $ estimate using cached pricing table
- **Broadcast / compare mode**: one prompt sent to multiple provider+model pairs simultaneously; responses shown side by side with latency and cost per result
- `POST /api/broadcast` — fan-out to selected models in parallel, collect results
- Frontend: model multi-select, side-by-side response cards with cost + latency badges

## Phase 9 — Polish _complete_
_Goal:_ Make the dashboard comfortable for daily use.
- Dark theme (CSS custom properties, toggle persisted in `localStorage`)
- Chart.js panel: tokens and estimated spend over time (daily/weekly aggregation from history log)
- Masked key display in the UI (last 4 chars only, never full key)
- Rate-limit header inspector: surface `x-ratelimit-*` values after each request runner call
- Streaming toggle on the request runner (SSE per provider) — validates streaming behaviour per provider
- Minor UX: loading spinners, error toasts, keyboard shortcut to run request
