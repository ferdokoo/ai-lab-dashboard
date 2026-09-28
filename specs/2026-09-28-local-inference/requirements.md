# Requirements: Local Inference (Ollama + LM Studio)

## Goal
Treat locally-running models as first-class providers alongside the five cloud providers. A developer can health-check, browse, and fire requests at Ollama and LM Studio from the same dashboard with no separate tooling.

## In Scope
- `backend/providers/ollama.py` probing `localhost:11434`
- `backend/providers/lmstudio.py` probing `localhost:1234` (OpenAI-compatible API)
- Both implement `health()`, `models()`, `request()` (reuse the OpenAI-compatible patterns already in the codebase where relevant)
- Both surface in health checks, model catalog, and request runner with no special-casing
- Frontend cards for Ollama and LM Studio alongside cloud providers, greying out gracefully when the server isn't running

## Out of Scope
- Streaming / SSE toggle for local providers
- Authentication for local servers
- Starting, installing, or downloading models (the server is assumed already running)
- Any changes to existing cloud provider modules

## Key Decisions
- Same interface (`health`, `models`, `balance`, `request`); no API key required
- Connection failure is surfaced clearly rather than swallowed — returned as an explicit "connection error" state
- Local providers return pricing/context-window values as `None` where unknown rather than guessing

## Context & Constraints
- Mission principle 4 (**Extensible by design**): new providers implement the same small interface with no routing or frontend changes
- Mission principle 2 (**Honest data**): show real data or say so explicitly — no placeholders
- Tech stack: use `httpx` for probes (SDKs reserved for request runner); no build step, vanilla JS frontend
- Runs on Windows native and WSL2 without modification (localhost binding must work in both)