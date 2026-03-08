# Memory Bank

This directory contains persistent context files for AI-assisted development sessions.

## Files

| File | Purpose | Scope |
|------|---------|-------|
| `projectbrief.md` | Goals, constraints, stakeholders, lessons | `[ALWAYS]` |
| `activeContext.md` | Current focus, blockers, recovery | `[SESSION]` |
| `SESSION.md` | Session index (append-only) | `[SESSION]` |
| `master-plan.md` | Milestones and roadmap | `[ALWAYS]` |
| `logs/` | Daily session logs | `[SEARCH]` |
| `archive/` | Archived entries | `[SEARCH]` |
| `plans/` | Implementation plans | `[SEARCH]` |

## Usage

1. Read files in order: `projectbrief.md` → `activeContext.md` → `SESSION.md` → `master-plan.md`
2. Update `activeContext.md` as focus changes
3. Append to `SESSION.md` at session start/end
4. Store plans in `plans/` directory

---
*Created: 2026-02-19*
