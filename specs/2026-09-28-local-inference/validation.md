# Validation: Local Inference (Ollama + LM Studio)

## Acceptance Criteria
- [ ] Ollama and LM Studio implement the full provider interface (`health`, `models`, `request`)
- [ ] Both providers are registered and appear in health checks, model catalog, and request runner with no routing/frontend special-casing
- [ ] Frontend cards grey out with a clear message when the local server is not running
- [ ] No API key is required for either provider

## Test Coverage
- [ ] pytest passes for: Ollama health up/down, LM Studio health up/down, model list parsing, and request round-trip (using mocked `httpx` responses)
- [ ] Connection-failure paths return an explicit error state rather than an unhandled exception
- [ ] Existing cloud provider tests still pass (no regressions)

## Manual Verification Steps
1. With Ollama **stopped**: open the dashboard — the Ollama card is greyed out with a "not running" message; health check reports failure with a clear reason.
2. Start Ollama (`ollama serve`) and run health check — card goes green with latency.
3. Open the model catalog — `ollama list` models appear; pricing columns are empty/honest (`None`).
4. Run a request from the request runner against a pulled local model — response text, token counts, and latency display correctly.
5. Repeat steps 1–4 for LM Studio (`localhost:1234`) with its OpenAI-compatible endpoint.

## Edge Cases
- Server not running (connection refused)
- Model requested but not pulled locally
- Slow local response / large model (timeout handling)
- Empty model list
- Non-default base URL/port for either server

## Merge Checklist
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] No regressions in cloud provider behavior