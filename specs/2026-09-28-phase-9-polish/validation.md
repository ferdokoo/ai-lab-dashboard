# Validation: Phase 9 — Polish

## Acceptance Criteria
- [ ] Four pages render and navigate correctly: Home (Health + Balance), Catalogue (Model Catalogue + Cost Calculator), Runner (Request Runner + Compare Mode), History
- [ ] Dark theme toggle works on all four pages and persists across reloads; no hardcoded colours remain
- [ ] Usage charts (tokens + estimated spend) render from history data with daily and weekly aggregation
- [ ] Keys are shown masked (last 4 chars only); full key is never visible in the UI
- [ ] `x-ratelimit-*` headers appear in the response panel after a request when the provider returns them
- [ ] Streaming toggle streams output incrementally for providers that support it, and degrades gracefully otherwise
- [ ] Loading spinners, error toasts, and the keyboard run shortcut all function

## Test Coverage
- Unit/route tests for the usage-aggregation endpoint (daily/weekly grouping) including empty-history case
- Request-runner route test asserting rate-limit headers are captured and returned when present
- Streaming endpoint test returning an SSE stream for a supported provider
- No regressions in existing phases: health, models, request, history, broadcast routes still pass

## Manual Verification Steps
1. `uvicorn backend.main:app`; open the app and confirm the four-page nav works
2. Toggle dark theme on Home; navigate all pages and reload to confirm persistence
3. Run a request against OpenAI/Anthropic/OpenRouter; confirm tokens/spend appear in the chart after refresh
4. Check a provider list; confirm keys are masked to last 4 chars
5. Run a request on a provider that returns `x-ratelimit-*` (e.g. OpenRouter/OpenAI); confirm headers show in the inspector
6. Enable streaming; confirm output streams progressively
7. Trigger a failing request; confirm an error toast appears and a spinner shows during in-flight calls
8. Press Ctrl/Cmd+Enter in the runner; confirm it submits the request

## Edge Cases
- Ollama / LM Studio offline — panels grey out cleanly, no broken charts or toasts
- Provider returns no `x-ratelimit-*` headers — inspector shows the honest "none returned" message
- Empty history log — charts show an empty state rather than errors
- Provider does not support streaming — falls back to a single non-streamed response
- Theme toggle with no saved value — defaults to light

## Merge Checklist
- [ ] All acceptance criteria met
- [ ] Automated tests passing
- [ ] No regressions across prior phases (health, models, request, history, broadcast)
- [ ] `uvicorn backend.main:app` single start command still works with no build step