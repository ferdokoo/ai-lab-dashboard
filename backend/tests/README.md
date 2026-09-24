# Backend Tests

Tests for the request-runner API live here. They run with no network access and
never touch the real database — every fixture redirects reads/writes to a
temporary SQLite file and every provider is swapped out for a stub.

## Running the tests

From the repository root:

```powershell
pytest
```

`testpaths = backend/tests` is already set in `pytest.ini`, so plain `pytest`
picks these up. Other useful invocations:

```powershell
pytest backend/tests                    # run this directory explicitly
pytest backend/tests/test_request_runner.py   # run a single file
pytest -v                               # verbose, one line per test
pytest -k openai                        # filter by test name
pytest -x                               # stop after the first failure
```

Dependencies (`pytest`, `pytest-asyncio`, and the project requirements) are
listed in `requirements.txt`.

## What's covered

`test_request_runner.py` has two groups of tests.

### Route tests (`TestClient`, stubbed providers)

These exercise the HTTP layer end-to-end via FastAPI's `TestClient` with
`PROVIDERS` monkeypatched to a `StubProvider`, so no live SDK call is made.

- `test_openai_request_route_returns_normalized_payload` — `POST /api/openai/request` returns the normalized payload.
- `test_request_log_row_written_on_success` — a success writes one row to the requests log (no body/prompt text is ever stored).
- `test_request_log_written_on_failure` — a provider error still writes a row, with `None` token counts.
- `test_empty_prompt_is_rejected_without_writing` — blank prompt returns `400` and logs nothing.
- `test_unknown_provider_returns_404` — unknown provider path returns `404`.
- `test_tavily_search_route_logs_distinctly` — `POST /api/tavily/search` logs `kind = "search"` with an empty model.
- `test_tavily_request_route_is_rejected` — Tavily does not expose a `/request` route (`400`).
- `test_empty_search_query_is_rejected` — blank search query returns `400` and logs nothing.

### Provider tests (mocked SDKs)

These call a provider's `request`/`search` method directly with the underlying
SDK client class monkeypatched, verifying normalization and honest token counts.

- `test_openai_provider_request_normalized` — fakes `openai.AsyncOpenAI`.
- `test_anthropic_provider_request_normalized` — fakes `anthropic.AsyncAnthropic`.
- `test_tavily_search_returns_honest_none_tokens` — fakes `httpx.AsyncClient`; Tavily reports `None` for token counts.

## Fixtures

`conftest.py` provides a single fixture, `tmp_db`, which monkeypatches
`backend.db.DB_PATH` to a per-test temporary file so the real
`data/dashboard.db` is never modified.