# Validation: History Log

## Acceptance Criteria
- [ ] `GET /api/history` returns rows from the `requests` table with correct shape, default-ordered by time descending.
- [ ] Filtering by `provider`, `model`, date range, and `limit`/`offset` narrows results correctly and returns a total count.
- [ ] Rows with `NULL` token/cost/latency return `null` (not `0`), and the frontend renders them honestly.
- [ ] CSV export returns valid CSV with correct headers, matches the filtered rows, and triggers a download (attachment disposition).
- [ ] The frontend History panel lists, filters, sorts, and exports past requests without a build step.

## Test Coverage
Add `backend/tests/test_history.py` using the `tmp_db` fixture:
- [ ] Empty history returns an empty list + zero total.
- [ ] Provider filter, model filter, and combined provider+model filter.
- [ ] Date-range filter (start, end, both).
- [ ] `limit`/`offset` pagination returns the correct page and correct total.
- [ ] NULL token/cost/latency rows serialize as `null`.
- [ ] CSV export: headers present, row count matches filtered query, and values containing commas/quotes are properly escaped.
- [ ] Existing suites (`test_request_runner`, `test_balance`, etc.) still pass — no regressions.

## Manual Verification Steps
1. Start the app (`uvicorn backend.main:app`) and run two or three requests across at least two providers.
2. Open the History panel; confirm the latest request appears first.
3. Filter by one provider, then by a model; confirm results narrow and the total updates.
4. Click "Export CSV"; confirm the file downloads, opens in Excel/VS Code, and matches the filtered table.
5. Run a Tavily search; confirm its history row shows honest blank/`null` token and cost cells.

## Edge Cases
- Empty log (fresh DB) — no crash, empty state message.
- Invalid/unknown `provider` or empty `model` filter values — no crash, sensible empty result.
- Large result sets — pagination prevents unbounded responses; `limit`/`offset` behave correctly near the end.
- `NULL` cost, tokens, and latency — serialized as `null` and rendered honestly.
- CSV values containing commas, quotes, or newlines — escaped per RFC 4180.

## Merge Checklist
- [ ] All acceptance criteria met.
- [ ] Backend test suite passing (including new `test_history.py`).
- [ ] No regressions in existing tests.
- [ ] CSV export opens correctly in a spreadsheet/editor.
- [ ] CHANGELOG updated (per project convention).