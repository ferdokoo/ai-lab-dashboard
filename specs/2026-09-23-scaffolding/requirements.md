# Requirements: Scaffolding

## Goal
Phase 1 creates the minimal working skeleton of the AI Lab Dashboard so that every subsequent phase has a reliable, runnable foundation to build on. There is currently no repo structure, no start command, and no working app — this phase delivers exactly that: a FastAPI server that starts cleanly, serves a static HTML page, and has a placeholder provider module that validates the shared interface shape.

## In Scope
- Repo directory layout: `backend/`, `frontend/`, `specs/`
- Python virtual environment and `requirements.txt` (pinned dependencies)
- `.env.example` documenting all expected key names
- `backend/config.py` loading `.env` via `python-dotenv`
- `backend/main.py` — FastAPI app with a single `GET /` route serving the static frontend page
- `frontend/index.html` — minimal static HTML5 placeholder page
- `backend/providers/placeholder.py` — stub implementing the interface shape (`health`, `models`, `balance`, `request`)
- `.gitignore` entry for `.env`

## Out of Scope
- Real provider integrations (health checks, model lists, balance, request runner)
- Frontend interactivity (no JavaScript logic, no buttons, no API calls from the browser)
- Database setup (SQLite — deferred to a later phase)
- Any provider SDK imports or usage
- CI/CD, Docker, or deployment configuration

## Key Decisions
- `uvicorn backend.main:app` is the single and only start command — no process manager, no build step.
- `config.py` must not raise an exception when `.env` is absent; all provider keys are optional at startup and default to `None`.
- The placeholder provider raises `NotImplementedError` on every method — it exists only to lock in the interface shape, not to run.
- Frontend is served directly from FastAPI (static file response) — no separate static server or bundler.

## Context & Constraints

**From mission.md:**
- Zero setup overhead is Principle 1: the server must start in under a minute on a fresh clone.
- Local-first: the server binds to `127.0.0.1` only; keys live in `.env` and never leave the machine.
- Extensible by design: the placeholder provider exists specifically to establish the shared interface (`health`, `models`, `balance`, `request`) that all future providers must implement.
- Must run on Windows (native Python) and WSL2 without code changes.

**From tech-stack.md:**
- Python 3.11+, FastAPI, uvicorn, python-dotenv — all required from day one.
- No React, Vue, or build tooling — vanilla HTML only.
- No Docker as a requirement.
- Provider SDKs are not needed for this phase (probe calls use `httpx`; SDKs are request-runner-only).
