---
name: changelog
description: Updates CHANGELOG.md in the project root with date headings and one bullet per commit. Use when the user asks to update the changelog, or when invoked before merging a branch or phase.
---

# Changelog

Maintain `CHANGELOG.md` in the project root. Structure: a `# Changelog` title, then one `## YYYY-MM-DD` heading per date (newest date first), with one bullet per commit under that date.

## Procedure

1. Check whether `CHANGELOG.md` exists in the project root.

### If it does not exist (bootstrap)

1. Run: `git log --date=short --pretty=format:"%ad%x1f%h%x1f%s"` (outputs date, short hash, subject — newest first).
2. Create `CHANGELOG.md` with the structure below, grouping every commit under its date heading.

### If it exists (incremental update)

1. Read `CHANGELOG.md` and collect the short hashes already recorded in bullets.
2. Run the same `git log` command.
3. For each commit whose short hash is not already recorded, append `- <subject> (<short hash>)` under the `## <commit date>` heading. Create the heading if missing, keeping dates in newest-first order.
4. Never rewrite or reorder existing bullets; only add new ones.

## Format

```markdown
# Changelog

## 2026-08-20
- feat: some change (abc1234)
- fix: another change (def5678)

## 2026-08-17
- initial commit (9999999)
```

## Rules

- Date format is `YYYY-MM-DD` (from `--date=short`); headings are ordered newest first.
- Bullet format is `- <commit subject> (<short hash>)`; the short hash makes duplicates detectable.
- Skip merge commits (subjects starting with `Merge `) — they duplicate the work already recorded.
- Only touch `CHANGELOG.md`; do not modify any other file.
- Do not commit the changelog yourself — the user commits it as part of the merge.
