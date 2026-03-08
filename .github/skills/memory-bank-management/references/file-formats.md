# File Formats Reference

Detailed specifications for each memory bank file.

---

## projectbrief.md

**Purpose:** Goals, constraints, stakeholders, lessons learned
**Scope:** `[ALWAYS]` — loaded in every session
**Update Frequency:** When project scope changes or lessons are distilled

### Required Sections

```markdown
# Project Brief

## Goal
[What is the primary objective of this project?]

## Constraints
- Platform: [e.g., VS Code + GitHub Copilot]
- Frameworks: [e.g., React, FastAPI]
- Dependencies: [Key libraries]

## Stakeholders
- [Who uses or maintains this project?]

## Definition of Done
- [ ] [Criterion 1]
- [ ] [Criterion 2]

---
## Lessons Learned
<!-- Append lessons here -->
- [P0][LESSON] [Description]

---
*Created: YYYY-MM-DD | Last Updated: YYYY-MM-DD*
```

---

## activeContext.md

**Purpose:** Current focus, blockers, recovery instructions
**Scope:** `[SESSION]` — loaded during active sessions
**Update Frequency:** Every session (on-init, on-end, pre-compact)

### Required Sections (4 Named Blocks)

```markdown
# Active Context

## Agent Context
[What the agent needs to know about itself, the project, and current conventions.
Include key constraints, tech stack, and any active rules.]

## Current Task
[What's being worked on right now. Single focus — update when switching tasks.]

## Pending
- [ ] [Checklist of open items, ordered by priority]
- [ ] [Each item should be actionable]

## Recovery Instructions
[What to do FIRST when loading this file after a context break.
Include: which file to read, what state to expect, what to do next.]

---
*Last Updated: YYYY-MM-DD*
```

---

## SESSION.md

**Purpose:** Summary index of all sessions (links to daily logs)
**Scope:** `[SESSION]` — loaded during active sessions
**Update Frequency:** Every session (append-only)

### Index Format

```markdown
# Session Log

## YYYY-MM-DD — vX.Y.Z
**Objective:** [What was the goal]

**Actions:**
- [What was done, step by step]

**Decisions:**
- [DEC] [Decision made and rationale]

**Lessons:**
- [LESSON] [What was learned]

**Status:** ✅ Complete | ⏳ In Progress | ❌ Blocked

---
```

### Two-Phase Recall

1. **Phase 1:** Agent scans the SESSION.md index to understand session history at a glance
2. **Phase 2:** If a specific session is relevant, agent reads the linked `logs/YYYY-MM-DD.md` file for full detail

---

## master-plan.md

**Purpose:** Milestones and roadmap
**Scope:** `[ALWAYS]` — loaded in every session
**Update Frequency:** When milestones change

### Required Sections

```markdown
# Master Plan

## Milestones
1. [ ] **Phase 1: [Name]** — [Description] (TASK-XXX–YYY)
2. [ ] **Phase 2: [Name]** — [Description] (TASK-XXX–YYY)

## Upcoming Work
- [ ] [Next immediate task]
- [ ] [Following task]

## Completed
- [x] [Completed milestone or task]

---
*Last Updated: YYYY-MM-DD*
```

---

## logs/YYYY-MM-DD.md

**Purpose:** Daily session logs with full detail
**Scope:** `[SEARCH]` — never auto-loaded; access on demand
**Update Frequency:** Every session (append to same-day file)

### Format

```markdown
# YYYY-MM-DD

## Session: vX.Y.Z
**Objective:** [What was the goal]

**Actions:**
- [What was done, step by step]

**Decisions:**
- [DEC] [Decision made and rationale]

**Lessons:**
- [LESSON] [What was learned]

**Status:** ✅ Complete | ⏳ In Progress | ❌ Blocked

---

## Session: vX.Y.Z+1
[Next session on the same day...]
```

---

## archive/sessions-YYYY.md

**Purpose:** Archived session entries
**Scope:** `[SEARCH]` — never auto-loaded
**Update Frequency:** When SESSION.md exceeds 20 entries

### Format

```markdown
# Archived Sessions (YYYY)

Archived from SESSION.md on YYYY-MM-DD

---

## YYYY-MM-DD — vX.Y.Z
[Archived session entry...]
```

---

## plans/YYYY-MM-DD-*.md

**Purpose:** Implementation plans
**Scope:** `[SEARCH]` — never auto-loaded
**Update Frequency:** When creating new plans

### Format

See `plan.prompt.md` for the standard plan structure.

---

## File Scope Summary

| File | Scope | When Loaded |
|------|-------|-------------|
| `projectbrief.md` | `[ALWAYS]` | Every session |
| `activeContext.md` | `[SESSION]` | Active work sessions |
| `SESSION.md` | `[SESSION]` | Active work sessions |
| `master-plan.md` | `[ALWAYS]` | Every session |
| `README.md` | `[ALWAYS]` | Every session |
| `logs/*.md` | `[SEARCH]` | On-demand |
| `archive/*.md` | `[SEARCH]` | On-demand |
| `plans/*.md` | `[SEARCH]` | On-demand |
