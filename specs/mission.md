# Mission: Local AI Lab Dashboard

## Problem
Developers and AI practitioners who work with multiple LLM providers (OpenAI, Anthropic, Gemini, OpenRouter, Tavily, and local inference servers) spend too much time juggling curl commands, per-provider dashboards, one-off scripts, and manual cost tracking. There is no single place to check key validity, browse model catalogs, fire test requests, or see what things cost — including models running locally on their own hardware.

## Goal
A single, lightweight local web app that lets you probe and exercise every LLM provider you use from one screen — health check a key, browse models and pricing, run a prompt, compare outputs, track spend — without leaving localhost and without a build step.

## Principles

1. **Zero setup overhead** — `uvicorn main:app` is the entire start command. No build tooling, no Docker required, no managed services. If it takes more than a minute to get running on a fresh clone, something is wrong.
2. **Honest data** — Display real numbers wherever the provider's API actually surfaces them. Where it doesn't (e.g. OpenAI/Anthropic account balance), say so explicitly and link out to the provider's billing page rather than showing a placeholder or a guess.
3. **Local-first & private** — The server binds to `127.0.0.1` only. Keys live in `.env` and never leave the machine. Logs store token counts and costs, not full prompt/response bodies (unless the user opts in).
4. **Extensible by design** — Every provider — cloud or local — implements the same small interface (`health`, `models`, `balance`, `request`). Adding a new provider should never require touching routing or frontend logic.

## Success Criteria

- One dashboard covers all five cloud providers plus Ollama and LM Studio with no separate tooling needed.
- A developer can go from "I have a new API key" to "I've confirmed it works, seen its model catalog, and run a test prompt" in under 60 seconds.
- Cost and token usage for every test call are logged locally and browsable over time.
- The app runs on Windows (native Python) and WSL2 without modification.
