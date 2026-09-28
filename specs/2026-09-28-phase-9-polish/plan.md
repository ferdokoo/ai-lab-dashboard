# Plan: Phase 9 — Polish

## 1. Four-Page Layout Refactor
- [ ] Define page sections (Home, Catalogue, Runner, History) and a client-side nav bar (vanilla JS, hash-based routing)
- [ ] Move Providers Health + Balance & Usage panels onto the **Home** page
- [ ] Move Model Catalogue + Cost Calculator onto the **Catalogue** page
- [ ] Move Request Runner + Compare Mode onto the **Runner** page
- [ ] Move History log (filters, sort, CSV export) onto the **History** page
- [ ] Preserve existing panel behaviour during the move; health checks, requests, and compare all still function per page

## 2. Dark Theme
- [ ] Introduce CSS custom properties for all colours (tokens for background, surface, text, accent, success/error)
- [ ] Add light-by-default theme + dark theme variable set
- [ ] Theme toggle control with state persisted in `localStorage`
- [ ] Verify all four pages respect theme with no hardcoded colours

## 3. Usage Chart Panel (Chart.js)
- [ ] Add usage-over-time endpoint (or frontend aggregation helper) grouping tokens + estimated spend by day and week from the history log
- [ ] Render tokens and estimated spend charts using Chart.js (one for tokens, one for spend)
- [ ] Handle empty history gracefully (empty-state message, no broken chart)

## 4. Masked Key Display
- [ ] Add masked key rendering (last 4 chars only) wherever keys are shown
- [ ] Ensure full key is never rendered to the DOM or sent in a way the UI can expose

## 5. Rate-Limit Header Inspector
- [ ] Capture `x-ratelimit-*` (and related) headers from provider responses in the request runner
- [ ] Surface captured headers in the response panel after each call
- [ ] Show a clear "no rate-limit headers returned" message when absent

## 6. Streaming Toggle
- [ ] Add streaming toggle to request runner (off by default)
- [ ] Implement SSE streaming per provider through the existing `request(model, prompt, options)` interface
- [ ] Stream output into the response panel incrementally; fall back to non-streamed on unsupported providers

## 7. Minor UX
- [ ] Add loading spinners to long-running actions (health check, request, broadcast, model fetch)
- [ ] Add error toasts for failed API calls
- [ ] Add keyboard shortcut to run the request (e.g. Ctrl/Cmd+Enter)