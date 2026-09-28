# AI Lab Dashboard

A lightweight, local-only web app for working with LLM providers from a single screen. Probe and exercise OpenAI, Anthropic, Gemini, OpenRouter, Tavily, Ollama, and LM Studio — check key health, browse model catalogs and pricing, fire test requests, compare outputs side by side, and track spend — all without leaving localhost and without any build step.

## Features

- **Health checks** — one card per provider that verifies key validity and endpoint reachability with latency.
- **Model catalog** — browse available models, context windows, and input/output pricing per provider, with live refresh.
- **Request runner** — send a prompt to any model, see the full response, token usage, and latency.
- **Local inference** — Ollama and LM Studio as first-class providers, no API key required.
- **Balance & usage** — real credit numbers where the API exposes them; honest "not available" messaging elsewhere.
- **History log** — browse, filter, and CSV-export every past request with token and cost data.
- **Cost tools & compare mode** — estimate costs before running, and broadcast one prompt to many models in parallel.
- **Polish** — dark theme, usage charts, masked keys, rate-limit inspection, and streaming.

## Tech Stack

- **Backend** — Python 3.11+, FastAPI, uvicorn, httpx, python-dotenv, aiosqlite.
- **Provider SDKs** — openai, anthropic, google-genai (request runner).
- **Frontend** — vanilla JavaScript (ES2020), HTML5, CSS3, Chart.js — no framework or bundler.
- **Storage** — SQLite (single file, no setup).

## Getting Started

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
Copy-Item .env.example .env
# then fill in the keys you want to use in .env

# 4. Run
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000 in your browser, or double-click `launch.bat` to start and open it automatically.

All keys are optional at startup — missing keys simply disable that provider. See `.env.example` for every supported variable, including the OpenRouter management key required for the balance endpoint.

## Project Structure

```
ai-lab-dashboard/
├── backend/                  # FastAPI application
│   ├── main.py               # App entrypoint; serves the frontend and mounts routers
│   ├── config.py             # Loads .env via python-dotenv
│   ├── cache.py              # SQLite-backed caching for model/pricing data
│   ├── cost.py               # Cost estimation helpers
│   ├── db.py                 # SQLite connection management
│   ├── history.py            # Request log schema and access
│   ├── pricing.py            # Price resolution (incl. Tavily search fallback)
│   ├── requestlog.py         # Request logging
│   ├── providers/            # One module per provider, shared interface
│   │   ├── base.py           # Abstract interface: health, models, balance, request
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── gemini.py
│   │   ├── openrouter.py
│   │   ├── tavily.py
│   │   ├── ollama.py
│   │   ├── lmstudio.py
│   │   └── placeholder.py
│   ├── routers/              # API endpoints
│   │   ├── health.py
│   │   ├── models.py
│   │   ├── request.py
│   │   ├── balance.py
│   │   ├── history.py
│   │   ├── cost.py
│   │   └── broadcast.py
│   └── tests/                # pytest suite
├── frontend/                 # Static frontend (no build step)
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── chart.umd.min.js      # Chart.js
├── data/                     # Local SQLite databases and CSV exports
├── specs/                    # Mission, tech stack, roadmap, and phase specs
├── scripts/
│   └── inspect_db.py         # Inspect local databases
├── requirements.txt          # Python dependencies
├── pytest.ini                # pytest configuration
├── .env.example              # Environment variable template
└── launch.bat                # One-click start on Windows
```

## Data & Privacy

- The server binds to `127.0.0.1` only and is not intended for network exposure.
- API keys live in `.env` (gitignored) and never leave the machine.
- The request log stores timestamps, provider, model, token counts, estimated cost, and latency — not full prompt/response bodies by default.

## Security

This tool is designed for **local use only**. Several deliberate trade-offs reflect that:

- **No authentication.** There is no login or API token. Anyone who can reach port 8000 can proxy requests through your API keys.
- **`GET /api/keys` is unauthenticated.** It returns the last four characters of each configured key to confirm presence — this is intentional for local convenience but would be a leak on a shared host.
- **The `options` field on request/broadcast endpoints is passed through to provider SDKs without an allowlist.** This is intentional flexibility for a lab tool but could trigger unexpected spend if the server were exposed.

### If you choose to expose this on a network

Do **not** run this on a public IP or shared machine without adding all of the following:

1. **Reverse proxy with authentication** (e.g. nginx + HTTP Basic Auth, or Authelia) in front of uvicorn. Never expose uvicorn directly.
2. **TLS** — keys must not travel over plain HTTP outside localhost.
3. **Firewall** — restrict port access to trusted IPs only.
4. **Change the bind address** in `launch.bat` / your uvicorn command from `--host 127.0.0.1` to the specific interface you intend to serve, never `0.0.0.0` on a machine with a public interface.
5. **Review the `/api/keys` endpoint** — consider removing the `masked` field or removing the route entirely.

The built-in CORS policy already restricts cross-origin browser requests to the dashboard's own origin (`127.0.0.1:8000` / `localhost:8000`). If you change the host or port, update `allow_origins` in `backend/main.py` to match.