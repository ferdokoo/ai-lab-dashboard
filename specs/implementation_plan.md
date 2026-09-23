# Local AI Lab Dashboard — Implementation Plan

## 1. Purpose

A single local web app that lets you probe and exercise every LLM/API provider you use (OpenAI, Gemini, Anthropic, OpenRouter, Tavily) from one screen — click a button, see if the key works, see what models cost, fire a test request, and track what you've spent — instead of juggling curl commands, provider dashboards, and one-off scripts.

## 2. Objectives

- One-click **health check** per provider (is the key valid, is the endpoint reachable)
- **Model catalog** per provider with pricing, refreshed on demand
- **Ad-hoc request runner** — pick a model, send a prompt, see the raw response, latency, and token usage
- **Balance / usage** visibility wherever the provider's API actually exposes it (see reality-check below — this is uneven across providers)
- **Local history/logging** of everything you've run, so patterns and costs are visible over time
- Lightweight enough to start with `uvicorn app:main` and forget about — no build step, no Docker required (though it'll run fine in your WSL2 setup if you want it there)

## 3. Reality check per provider (this matters before you build feature #4/#5)

I checked current docs for each — the "balance" and "usage" story is not uniform, so it's worth knowing this before you design the UI around it:

| Feature | OpenAI | Anthropic | Gemini | OpenRouter | Tavily |
|---|---|---|---|---|---|
| Health check | ✅ cheap call, e.g. `GET /v1/models` | ✅ `GET /v1/models` | ✅ `models.list` | ✅ `GET /api/v1/models` | ✅ `GET /usage` |
| Model list | ✅ | ✅ | ✅ | ✅ | n/a |
| **Prices in the API response** | ❌ not returned — you must hardcode a pricing table | ❌ same | ❌ same | ✅ `/models` includes per-model pricing | n/a |
| **Account balance** | ❌ no endpoint works with a normal API key (old billing endpoints are dead; the real Usage/Costs API needs a separate admin key an org owner mints) | ❌ same story — usage/cost reports live under an admin-key-only org endpoint | ❌ no key-based endpoint; only via Cloud Billing API with a service account | ✅ `Returns the authenticated user's total credits purchased and total credits used` — but note current docs say "Only management keys can fetch credits", so you may need a separate management key from OpenRouter settings, not your normal inference key | ✅ `GET /usage` returns both per-key usage/limit and account plan usage/limit — the cleanest of the bunch |
| Per-request token usage | ✅ in response body | ✅ in response body | ✅ in response body | ✅ in response body | n/a (credit-based) |

**Practical takeaway:** design "balance" as "best effort, per provider" rather than a uniform field. OpenRouter and Tavily will give you real numbers; for OpenAI/Anthropic/Gemini, the honest move is to show per-request token usage (which you do get) and a link out to their billing dashboard for account balance, rather than pretending you can fetch it.

## 4. Technical stack

Given you're already comfortable in Python (venvs, Jupyter, WSL2 Docker work) and have built HTML+Chart.js visuals before, I'd keep this all-Python + vanilla frontend rather than pulling in Node/React:

- **Backend:** Python + **FastAPI** + `uvicorn`. Gives you async calls (nice when pinging 5 providers at once), free OpenAPI docs at `/docs` as a bonus reference, and no framework weight.
- **HTTP calls to providers:** `httpx` (async) directly against each provider's REST endpoints for health/model-list/balance calls — one uniform pattern instead of five different SDKs with their own version churn. Use the official SDKs (`openai`, `anthropic`, `google-genai`) only for the "send a real request" feature, since they handle streaming and error shapes better than raw REST for that one job.
- **Frontend:** a single static page — plain HTML + vanilla JS (`fetch` to your local FastAPI routes) + **Chart.js** for any usage-over-time charts (you already know the library). No build tooling needed.
- **Storage:** **SQLite** (via `aiosqlite` or stdlib `sqlite3`) — one file, zero setup, enough for a request log and cached model/pricing data.
- **Secrets:** `.env` + `python-dotenv`, gitignored. Server binds to `127.0.0.1` only — no reason to expose it on the network.

## 5. Architecture

```
ai-lab-dashboard/
├── backend/
│   ├── main.py            # FastAPI app + routes
│   ├── providers/
│   │   ├── base.py        # common interface: health(), models(), balance(), request()
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── gemini.py
│   │   ├── openrouter.py
│   │   └── tavily.py
│   ├── pricing.py         # static/cached pricing tables for providers that don't expose price
│   ├── db.py               # SQLite logging (requests, tokens, cost, latency)
│   └── config.py          # loads .env
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── .env.example
└── requirements.txt
```

Each provider module implements the same small interface, so the frontend and routing code never need to know provider-specific details.

## 6. Implementation phases

1. **Scaffolding** — repo layout, venv, `.env` template, a "hello world" FastAPI serving the static page. Prove the loop works end to end with one provider.
2. **Health checks** — one button per provider, cheapest possible probe call, green/red status + response time.
3. **Model catalog** — fetch + cache each provider's model list; merge in your local pricing table where the API doesn't supply price; render as a sortable table.
4. **Request runner** — form to pick provider + model, send a prompt, show the raw response, latency, and token usage pulled from the response body.
5. **Local inference (Ollama + LM Studio)** — add `ollama.py` and `lmstudio.py` provider modules using their OpenAI-compatible REST APIs. No key required. Both providers appear in health checks, the model catalog, and the request runner. Cards are greyed out gracefully when the local server isn't running.
6. **Balance/usage panel** — real numbers for OpenRouter and Tavily; for the others, show last-known per-request token totals plus a link to that provider's billing page instead of faking a number.
7. **Local history** — SQLite log of every test call (timestamp, provider, model, tokens, estimated cost, latency); a simple filterable table in the UI with CSV export.
8. **Cost tools & compare mode** — a calculator (token counts → $ using the cached pricing table) and a broadcast mode: same prompt to several providers/models at once, shown side by side with cost and latency.
9. **Polish** — dark theme, a Chart.js panel for spend/tokens over time, masked key display, rate-limit header inspector, streaming toggle on the request runner.

Each phase is independently useful, so you can stop after any of them and already have something usable.

## 7. Extra ideas (post-roadmap)

- **Response regression check** — pin a "golden" response for a prompt and flag when a model update changes the answer meaningfully
- **llama.cpp server support** — lower-level local inference option; also OpenAI-compatible
- **Multi-user / team mode** — shared history log with per-user key isolation (out of scope for a local dev tool, but worth noting)

## 8. Security notes

Local-only by default (`127.0.0.1` binding), keys never leave `.env`, `.gitignore` covers it, and logs should store token counts/costs, not full prompt/response bodies, unless you deliberately want a request archive.

---
