# Plan: Balance & Usage Panel

## 1. Balance interface & normalization
- [x] Define the normalized `balance()` return shape in `backend/providers/base.py` (normalized fields + optional `raw` payload) and document it in the docstring
- [x] Confirm every provider module implements `balance()` (real data or `None`)

## 2. Provider implementations
- [x] OpenRouter: fetch credit/usage via the management key (`OPENROUTER_MANAGEMENT_KEY`); return normalized fields + raw; report "management key not configured" when only the inference key is present
- [x] Tavily: fetch `GET /usage` returning per-key and account-plan usage; normalize into the shared shape
- [x] OpenAI / Anthropic / Gemini: `balance()` returns `None`

## 3. Routing & response envelope
- [x] Add `GET /api/{provider}/balance` route
- [x] For real-data providers, return the normalized balance payload
- [x] For `None`-returning providers, return an explicit "not available via API" state with a billing link rather than an error or empty object

## 4. Frontend panel
- [x] Add a balance panel per provider (local providers Ollama/LM Studio excluded — nothing to report)
- [x] Real-data providers show the normalized balance/usage values
- [x] Unsupported providers show an honest "not available via API" message plus a link to the provider's billing page (and surface per-request token totals where available)

## 5. Tests
- [x] pytest coverage mocking OpenRouter balance (with and without management key)
- [x] pytest coverage mocking Tavily `/usage`
- [x] pytest coverage asserting OpenAI/Anthropic/Gemini return `None`
- [x] Route tests covering both the real-data and "not available" response envelopes
- [x] No regressions in existing health/models/request tests

## 6. Docs
- [x] Update `.env.example` if any new keys are needed (management key already present — verify wording)