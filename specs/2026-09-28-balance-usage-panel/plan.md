# Plan: Balance & Usage Panel

## 1. Balance interface & normalization
- [ ] Define the normalized `balance()` return shape in `backend/providers/base.py` (normalized fields + optional `raw` payload) and document it in the docstring
- [ ] Confirm every provider module implements `balance()` (real data or `None`)

## 2. Provider implementations
- [ ] OpenRouter: fetch credit/usage via the management key (`OPENROUTER_MANAGEMENT_KEY`); return normalized fields + raw; report "management key not configured" when only the inference key is present
- [ ] Tavily: fetch `GET /usage` returning per-key and account-plan usage; normalize into the shared shape
- [ ] OpenAI / Anthropic / Gemini: `balance()` returns `None`

## 3. Routing & response envelope
- [ ] Add `GET /api/{provider}/balance` route
- [ ] For real-data providers, return the normalized balance payload
- [ ] For `None`-returning providers, return an explicit "not available via API" state with a billing link rather than an error or empty object

## 4. Frontend panel
- [ ] Add a balance panel per provider
- [ ] Real-data providers show the normalized balance/usage values
- [ ] Unsupported providers show an honest "not available via API" message plus a link to the provider's billing page (and surface per-request token totals where available)

## 5. Tests
- [ ] pytest coverage mocking OpenRouter balance (with and without management key)
- [ ] pytest coverage mocking Tavily `/usage`
- [ ] pytest coverage asserting OpenAI/Anthropic/Gemini return `None`
- [ ] Route tests covering both the real-data and "not available" response envelopes
- [ ] No regressions in existing health/models/request tests

## 6. Docs
- [ ] Update `.env.example` if any new keys are needed (management key already present — verify wording)