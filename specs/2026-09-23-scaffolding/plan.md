# Plan: Scaffolding

## 1. Environment Setup
- [x] Create Python virtual environment (`python -m venv .venv`)
- [x] Create `requirements.txt` with pinned versions: `fastapi`, `uvicorn[standard]`, `httpx`, `python-dotenv`
- [x] Verify `pip install -r requirements.txt` completes without errors

## 2. Configuration
- [x] Create `.env.example` documenting all expected key names (one per cloud provider)
- [x] Create `backend/config.py` that loads `.env` via `python-dotenv` and exposes settings; must not crash if `.env` is absent (use defaults or `None` for optional keys)

## 3. Backend App
- [x] Create `backend/__init__.py` (empty, marks package)
- [x] Create `backend/main.py` with a FastAPI app instance
- [x] Add a `GET /` route that serves `frontend/index.html` as a static HTML response
- [x] Verify `uvicorn backend.main:app` starts with zero errors or warnings

## 4. Frontend Placeholder
- [x] Create `frontend/index.html` — minimal valid HTML5 page with a heading confirming the app is running (e.g. "AI Lab Dashboard")
- [x] No JavaScript logic required; static markup only

## 5. Placeholder Provider
- [x] Create `backend/providers/__init__.py` (empty)
- [x] Create `backend/providers/placeholder.py` implementing stub methods matching the intended interface shape: `health()`, `models()`, `balance()`, `request()` — each raises `NotImplementedError`
- [x] Confirm the module imports without errors

## 6. Repo Layout Verification
- [x] Confirm directory structure matches: `backend/`, `frontend/`, `specs/`
- [x] Confirm `.env.example` is present and `.env` is in `.gitignore`
