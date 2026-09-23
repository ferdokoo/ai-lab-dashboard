---
name: feature-spec
description: Use when the user asks to start a new feature, spec out the next phase, or plan the next roadmap item. Reads specs/roadmap.md to find the next phase, creates a git branch, asks grouped questions about the feature, then writes specs/YYYY-MM-DD-feature-name/{plan.md,requirements.md,validation.md}.
---

# Skill: feature-spec

## When to trigger

Use this skill when the user says things like:
- "start the next feature"
- "spec the next phase"
- "plan the next roadmap item"
- "feature spec"
- "next phase"

## Workflow

### Step 1 — Read context (do NOT write anything yet)

Read all three of these files before doing anything else:

- `specs/roadmap.md` — identify the **next incomplete phase** (the first phase not yet marked done/complete)
- `specs/mission.md` — understand project purpose and principles
- `specs/tech-stack.md` — understand technology choices and constraints

Extract from the roadmap:
- The phase name and number
- A short slug for the branch/folder name (lowercase, hyphen-separated)
- Today's date in `YYYY-MM-DD` format

### Step 2 — Create a git branch

Create a branch named after the feature:

```
git checkout -b feature/<slug>
```

Report the branch name to the user.

### Step 3 — Ask grouped questions (REQUIRED before any file writes)

You MUST ask the user questions grouped into exactly these 3 categories before writing any files to disk. Use the Question tool and group them clearly:

**Group A — Requirements & Scope**
- What is the core user problem this phase solves?
- What is explicitly out of scope for this phase?
- Are there any key decisions or constraints already made?

**Group B — Plan & Tasks**
- Are there any known subtasks or implementation steps to include?
- Any ordering constraints or dependencies between tasks?
- Rough effort estimate or time budget?

**Group C — Validation & Success**
- How will you know the feature is working correctly?
- What does a successful merge look like (tests, manual checks, metrics)?
- Any edge cases or failure modes to validate against?

Wait for the user's answers before proceeding.

### Step 4 — Write spec files

Create the directory: `specs/YYYY-MM-DD-<slug>/`

Write these three files using the user's answers plus context from mission.md and tech-stack.md:

#### `plan.md`

A series of numbered task groups. Example structure:

```markdown
# Plan: <Feature Name>

## 1. <Task Group Name>
- [ ] Task description
- [ ] Task description

## 2. <Task Group Name>
- [ ] Task description
```

Keep tasks concrete and actionable. Reference the tech stack where relevant.

#### `requirements.md`

Scope, decisions, and context. Example structure:

```markdown
# Requirements: <Feature Name>

## Goal
One paragraph on what this phase achieves and why.

## In Scope
- ...

## Out of Scope
- ...

## Key Decisions
- ...

## Context & Constraints
References to mission.md principles and tech-stack.md choices that apply.
```

#### `validation.md`

How to know the implementation succeeded. Example structure:

```markdown
# Validation: <Feature Name>

## Acceptance Criteria
- [ ] Criterion

## Test Coverage
What tests must pass or be written.

## Manual Verification Steps
Step-by-step checks a human can perform.

## Edge Cases
Known edge cases to test.

## Merge Checklist
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] No regressions
```

### Step 5 — Confirm

Tell the user:
- The branch name
- The spec directory created
- A one-sentence summary of the feature scope

## Important rules

- Never write files before asking the grouped questions in Step 3.
- Always read `specs/mission.md` and `specs/tech-stack.md` before writing — they shape the content.
- Keep `plan.md` task-focused, `requirements.md` decision-focused, `validation.md` verification-focused.
- Use the actual date (check environment or use `git log --date=short -1` as a fallback).
