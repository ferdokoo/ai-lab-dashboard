---
name: project-spec
description: Use when the user wants to start a new project, initialize a specs directory, or generate a project constitution. Creates specs/mission.md, specs/tech-stack.md, and specs/roadmap.md after asking grouped questions about the project. Trigger phrases: "start a project", "init specs", "project spec", "generate specs", "create a constitution", "new project".
---

# Skill: project-spec

## When to trigger

Use this skill when the user says things like:
- "start a new project"
- "init specs" / "initialize specs"
- "project spec"
- "generate specs"
- "create a constitution"
- "set up the specs directory"

The user may also provide a source file (e.g. a README, brief, or notes file) to seed the answers.

## Workflow

### Step 1 — Check for a source file

If the user has provided a file path or document as input, read it now and extract as much context as possible to pre-fill your answers. Note which gaps remain.

If no source file is provided, proceed with all questions open.

### Step 2 — Ask grouped questions (REQUIRED before any file writes)

You MUST use the Question tool and ask all questions grouped into exactly these 3 categories before writing any files to disk.

Pre-fill answers from a source file where available, but still confirm them with the user.

---

**Group A — Mission**
- What is the project called?
- What problem does it solve, and for whom?
- What are the 2–3 core principles or values that should guide every decision?
- What does success look like at a high level?

**Group B — Tech Stack**
- What language(s) and runtime(s) will be used?
- What frameworks, libraries, or platforms are chosen (or under consideration)?
- What is the data storage approach (database, files, cloud)?
- Any infrastructure, deployment, or tooling decisions already made?
- Any hard constraints (must use X, must avoid Y)?

**Group C — Roadmap**
- What are the major capabilities the project needs to deliver?
- What is the suggested implementation order? (Think in small, shippable phases)
- Are there any known dependencies between phases?
- What is phase 1 — the smallest useful slice of the product?

---

Wait for the user's answers before proceeding.

### Step 3 — Write the spec files

Create the `specs/` directory if it does not exist.

Write these three files:

#### `specs/mission.md`

```markdown
# Mission: <Project Name>

## Problem
Who has this problem and what it is.

## Goal
One paragraph: what the project does and for whom.

## Principles
Guiding values that should inform every technical and product decision.
1. ...
2. ...
3. ...

## Success Criteria
What "done" looks like at the project level.
```

#### `specs/tech-stack.md`

```markdown
# Tech Stack: <Project Name>

## Languages & Runtimes
- ...

## Frameworks & Libraries
- ...

## Data Storage
- ...

## Infrastructure & Deployment
- ...

## Constraints
Things we must use or must avoid, and why.

## Open Decisions
Tech choices not yet finalized (remove entries as they are decided).
```

#### `specs/roadmap.md`

Phases must be small and shippable — each one should represent a focused, mergeable unit of work, not a multi-week epic.

```markdown
# Roadmap: <Project Name>

## Phase 1 — <Name>
_Goal:_ One sentence on what this unlocks.
- ...

## Phase 2 — <Name>
_Goal:_ One sentence on what this unlocks.
- ...

## Phase N — <Name>
_Goal:_ ...
- ...
```

Mark phases with `[x]` prefix once complete, e.g. `## [x] Phase 1 — <Name>`.

### Step 4 — Confirm

Tell the user:
- The three files created
- A one-sentence summary of Phase 1 (the first thing to build)
- The command to start the next feature: trigger the `feature-spec` skill

## Important rules

- Never write files before completing Step 2 (grouped questions).
- If a source file was provided, read it before asking questions and use it to reduce the question burden — but always confirm key answers.
- Keep `mission.md` principle-focused, `tech-stack.md` decision-focused, `roadmap.md` sequence-focused.
- Roadmap phases must be small. If a phase feels large, split it.
- Do not invent tech choices — only write what the user confirmed.
