# Validation: Scaffolding

## Acceptance Criteria
- [ ] `uvicorn backend.main:app` starts with zero errors and zero warnings
- [ ] `GET http://127.0.0.1:8000/` returns HTTP 200 and the content of `frontend/index.html`
- [ ] The page is visible and readable in a browser at `http://127.0.0.1:8000/`
- [ ] `.env.example` is present and documents every expected provider key name
- [ ] `.env` is listed in `.gitignore` (or `.env` does not exist and a new one can be created from `.env.example`)
- [ ] `backend/providers/placeholder.py` imports without errors
- [ ] `backend/config.py` loads without raising an exception when `.env` is absent

## Test Coverage
No automated test suite is required for this phase. The acceptance gate is a clean server start.

If a smoke test is added later, it should:
- Import `backend.main` without errors
- Assert that the FastAPI app object exists and has at least one route registered

## Manual Verification Steps
1. Clone the repo (or work from the project root).
2. Create and activate the virtual environment: `python -m venv .venv` then `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (WSL2/macOS).
3. Install dependencies: `pip install -r requirements.txt` — confirm no errors.
4. Do **not** create a `.env` file yet (tests the missing-`.env` edge case).
5. Run: `uvicorn backend.main:app` — confirm the output shows `Application startup complete` with no errors or tracebacks.
6. Open `http://127.0.0.1:8000/` in a browser — confirm the placeholder HTML page loads.
7. Create `.env` from `.env.example`, leave all values empty, and restart — confirm the server still starts cleanly.

## Edge Cases
- **Missing `.env` file** — `backend/config.py` must not raise `KeyError` or crash; all keys should fall back to `None` or an empty string. The server must start regardless.
- **Empty `.env`** — Same as above; all keys present but with empty values should not cause startup failures.

## Merge Checklist
- [ ] All acceptance criteria above are met
- [ ] `uvicorn backend.main:app` starts cleanly with no `.env` present
- [ ] `uvicorn backend.main:app` starts cleanly with a fully empty `.env`
- [ ] Browser confirms `GET /` returns the placeholder page
- [ ] `.env.example` covers all provider key names that will be needed in later phases
- [ ] No secrets committed (`.env` absent from git history)
- [ ] Directory structure matches `backend/`, `frontend/`, `specs/` as specified in the roadmap
