# Tech Stack: Local AI Lab Dashboard

## Languages & Runtimes
- Python 3.11+ (backend)
- Vanilla JavaScript (ES2020, no transpilation) + HTML5 + CSS3 (frontend)

## Frameworks & Libraries

**Backend**
- `FastAPI` — async web framework; free OpenAPI docs at `/docs` as a bonus
- `uvicorn` — ASGI server; single start command, no process manager needed
- `httpx` — async HTTP client for all provider probe calls (health, model list, balance)
- `python-dotenv` — loads `.env` into the environment at startup

**Provider SDKs** (request runner only — where streaming and error shapes matter)
- `openai` — OpenAI + OpenRouter (OpenAI-compatible)
- `anthropic` — Anthropic Claude
- `google-genai` — Gemini

**Frontend**
- Vanilla `fetch` against local FastAPI routes — no framework, no bundler
- `Chart.js` — usage-over-time charts (already familiar)

## Data Storage
- **SQLite** — single `.db` file, zero setup
- Access via `aiosqlite` (async) for request log and cached model/pricing data
- Stores: timestamp, provider, model, prompt tokens, completion tokens, estimated cost, latency ms
- Does **not** store full prompt/response bodies by default

## Infrastructure & Deployment
- Local only — server binds to `127.0.0.1`; not intended for network exposure
- Secrets in `.env`, gitignored via `.env.example` template
- Compatible with Windows (native Python) and WSL2 without code changes
- No Docker required (though it runs fine in Docker/WSL2 if desired)
- No CI/CD pipeline — local dev tool

## Constraints

| Must use | Reason |
|---|---|
| Python backend | Existing comfort; no Node runtime to install |
| SQLite | Zero-setup persistent storage; single file |
| `httpx` for probes | Uniform async pattern across all providers |
| `.env` for secrets | Keys never hardcoded or committed |

| Must avoid | Reason |
|---|---|
| React / Vue / build tooling | Adds install friction and a build step |
| Docker as a requirement | Adds friction for a local-only dev tool |
| Provider SDKs for probes | Version churn; unnecessary for simple REST calls |
| Storing full prompt/response bodies by default | Privacy; log sizes |

## Open Decisions
- Whether to support a streaming toggle in the request runner (SSE per provider) — noted as a desirable extra, not yet scoped
- Whether to surface `x-ratelimit-*` headers in the response inspector
- CSV export format for the history log
