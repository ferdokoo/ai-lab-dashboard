# Requirements: Phase 9 — Polish

## Goal
Turn the dashboard from a functional single-screen tool into something comfortable to use daily. This phase wraps up the roadmap with cosmetic polish (dark theme, masked keys, loading/error states), deeper insight (tokens and spend over time), and provider-behaviour visibility (rate-limit headers, streaming), while reorganising the panels into four focused pages so the app scales beyond one crowded screen.

## In Scope
- **Four-page layout** (SPA with client-side navigation):
  1. **Home** — Providers Health + Balance & Usage panels
  2. **Catalogue** — Model Catalogue + Cost Calculator
  3. **Runner** — Request Runner + Compare Mode
  4. **History** — History log (filters, sort, CSV export)
- **Dark theme** via CSS custom properties, toggle persisted in `localStorage`, light theme still default
- **Chart.js panel** for tokens and estimated spend over time (daily/weekly aggregation from the history log)
- **Masked key display** — last 4 characters only, never the full key
- **Rate-limit header inspector** — surface `x-ratelimit-*` values after each request runner call
- **Streaming toggle** on the request runner (SSE per provider), off by default
- **Minor UX** — loading spinners, error toasts, keyboard shortcut to run request

## Out of Scope
- Auth, accounts, multi-user, or shared access — stays single-user localhost
- New providers (existing seven: OpenAI, Anthropic, Gemini, OpenRouter, Tavily, Ollama, LM Studio only)
- Realtime/live-push dashboards (no WebSocket-driven auto-refresh beyond the streaming toggle itself)

## Key Decisions
- Dark theme implemented with CSS custom properties (no compile step); toggle stored in `localStorage`
- Streaming is an opt-in toggle on the request runner, defaulting to off
- Rate-limit headers surfaced only when the provider actually returns them (honest-data principle)

## Context & Constraints
- **Mission principles**: Zero setup overhead (no build step, `uvicorn main:app` still the whole start command); honest data (never fabricate rate-limit values or balances); extensible by design (streaming must plug into the existing `request(model, prompt, options)` provider interface, not bypass it).
- **Tech stack**: Vanilla JS/HTML/CSS frontend — page navigation is client-side only, no framework or bundler. `Chart.js` is the one permitted new dependency (already listed). SQLite history log already stores `timestamp, provider, model, prompt_tokens, completion_tokens, estimated_cost_usd` — charts aggregate from it; no schema change required unless a daily/weekly rollup helper is added server-side.
- Streaming stays per-provider SSE; provider SDKs (`openai`, `anthropic`, `google-genai`) are already used where streaming matters.