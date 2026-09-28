# Plan: Phase 9 — Polish

## 1. Four-Page Layout Refactor
- [x] Define page sections (Home, Catalogue, Runner, History) and a client-side nav bar (vanilla JS, hash-based routing)
- [x] Move Providers Health + Balance & Usage panels onto the **Home** page
- [x] Move Model Catalogue + Cost Calculator onto the **Catalogue** page
- [x] Move Request Runner + Compare Mode onto the **Runner** page
- [x] Move History log (filters, sort, CSV export) onto the **History** page
- [x] Preserve existing panel behaviour during the move; health checks, requests, and compare all still function per page

## 2. Dark Theme
- [x] Introduce CSS custom properties for all colours (tokens for background, surface, text, accent, success/error)
- [x] Add light-by-default theme + dark theme variable set
- [x] Theme toggle control with state persisted in `localStorage`
- [x] Verify all four pages respect theme with no hardcoded colours

## 3. Usage Chart Panel (Chart.js)
- [x] Add usage-over-time endpoint (or frontend aggregation helper) grouping tokens + estimated spend by day and week from the history log
- [x] Render tokens and estimated spend charts using Chart.js (one for tokens, one for spend)
- [x] Handle empty history gracefully (empty-state message, no broken chart)

## 4. Masked Key Display
- [x] Add masked key rendering (last 4 chars only) wherever keys are shown
- [x] Ensure full key is never rendered to the DOM or sent in a way the UI can expose

## 5. Rate-Limit Header Inspector
- [x] Capture `x-ratelimit-*` (and related) headers from provider responses in the request runner
- [x] Surface captured headers in the response panel after each call
- [x] Show a clear "no rate-limit headers returned" message when absent

## 6. Streaming Toggle
- [x] Add streaming toggle to request runner (off by default)
- [x] Implement SSE streaming per provider through the existing `request(model, prompt, options)` interface
- [x] Stream output into the response panel incrementally; fall back to non-streamed on unsupported providers

## 7. Minor UX
- [x] Add loading spinners to long-running actions (health check, request, broadcast, model fetch)
- [x] Add error toasts for failed API calls
- [x] Add keyboard shortcut to run the request (e.g. Ctrl/Cmd+Enter)