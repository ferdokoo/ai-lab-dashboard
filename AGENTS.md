# AGENTS.md

Guidance for AI coding assistants (Claude Code, Cursor, Copilot, etc.) working in this repository.

## What this project is

A local-only web dashboard ("AI Lab Dashboard") for probing and exercising LLM providers — OpenAI, Anthropic, Gemini, OpenRouter, Tavily, Ollama, and LM Studio — from a single screen. See `README.md` for the full feature set and folder structure.

- Backend: Python 3.11+ / FastAPI / SQLite (`backend/`)
- Frontend: vanilla JS/HTML/CSS, no build step (`frontend/`)
- Specs and roadmap live in `specs/`

## Spec-driven development

This project was built using the spec-driven skills in `.agents/skills/`. Respect that workflow — don't jump straight to code for new features or phases.

### Available skills

| Skill | Purpose |
|---|---|
| `project-spec` | Start a new project: writes `specs/mission.md`, `specs/tech-stack.md`, `specs/roadmap.md` after grouped questions. |
| `feature-spec` | Start the next feature/phase: reads the roadmap, creates a git branch, asks grouped questions, then writes `specs/YYYY-MM-DD-feature-name/{plan.md,requirements.md,validation.md}`. |
| `changelog` | Update `CHANGELOG.md` with one bullet per commit before merging a branch/phase. |

Each skill's `SKILL.md` (in `.agents/skills/<name>/`) contains the full workflow. Load the relevant skill before doing that kind of work.

### Workflow expectations

1. **New feature work** → load the `feature-spec` skill. It reads `specs/roadmap.md` to find the next incomplete phase, creates a `feature/<slug>` branch, asks grouped questions, and writes phase specs. Do not begin implementation until those spec files exist.
2. **Before merging a phase** → load the `changelog` skill to update `CHANGELOG.md`.
3. **New project / constitution** → load the `project-spec` skill.

## Conventions

- Follow the single shared provider interface (`health`, `models`, `balance`, `request`) when adding any provider. Extend `backend/providers/` without touching routing or frontend logic.
- Keep secrets in `.env` (gitignored); use `.env.example` as the template. Never commit keys.
- Don't store full prompt/response bodies in the log by default.
- Backend tests use pytest (see `pytest.ini`); the frontend has no build/lint step.

## Commands

```powershell
# Install
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Test
.venv\Scripts\python.exe -m pytest
```