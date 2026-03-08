---
name: memory-bank-management
description: "Persistent cross-session memory management for AI agents. v1.0.0 COMPLETE with Obsidian integration, three-space architecture, and automated processing pipeline. Load when working with memory bank files, session logs, lifecycle hooks, activeContext, pre-compact operations, SESSION.md, projectbrief, master-plan, or memory-bank/ directory conventions. Provides templates for initialization, Python scripts for automation (use uv run), priority tags (P0/P1/P2), type tags (DEC/FACT/PREF/LESSON), deduplication, archiving, and reference documentation. NEW: MOC files, processing scripts (reduce/reflect/reweave/rethink), Obsidian templates, and Dataview integration."
---

# Memory Bank Management — v1.0.0

## Status: ✅ Production Ready

**Version:** v1.0.0 (2026-02-20)  
**Implementation Status:** COMPLETE — All 16 tasks across 5 phases delivered and verified

**What's Included:**
- ✅ **Architecture:** Three-space conceptual model (self/notes/ops) with MOC navigation files
- ✅ **Processing Pipeline:** 4 automation scripts (reduce/reflect/reweave/rethink) for knowledge distillation
- ✅ **Obsidian Integration:** Templates, Dataview frontmatter schema, central dashboard
- ✅ **Automation Hooks:** Session-start, write-validation, auto-commit JSON configurations
- ✅ **Documentation:** Enhanced README, lifecycle guides, sensitivity markers, dedup conventions

---

## Overview

The memory bank (`memory-bank/`) is the persistent cross-session state store for AI-assisted development. This skill defines all conventions for reading, writing, and maintaining memory bank files.

**Bundled Resources:**
- `templates/` — Starter files (5 core files + daily-log)
- `templates.obsidian/` — Obsidian-specific templates with callouts/Dataview
- `scripts/` — Python automation (7 scripts, use `uv run`)
  - Lifecycle: `init_memory_bank.py`, `validate_memory_bank.py`, `archive_sessions.py`, `sync_context.py`
  - Processing Pipeline: `reduce_sessions.py`, `reflect.py`, `reweave.py`, `rethink.py`
- `references/` — Progressive disclosure documentation

---

## Processing Pipeline — 6 R's Model (v1.0.0)

Systematic knowledge distillation across sessions:

| Step | Script | Purpose |
|------|--------|---------|
| **1. RECORD** | (Manual) | Capture to daily logs + `SESSION.md` |
| **2. REDUCE** | `reduce_sessions.py` | Extract insights, decisions, blockers |
| **3. REFLECT** | `reflect.py` | Find connections to plans |
| **4. REWEAVE** | `reweave.py` | Backward-link to archive |
| **5. VERIFY** | (Manual) | Validate and approve |
| **6. RETHINK** | `rethink.py` | Challenge assumptions |

---

## Quick Start

### Initialize a New Memory Bank

```bash
cd .github/skills/memory-bank-management/scripts
uv run init_memory_bank.py /path/to/project
```

### Validate Memory Bank State

```bash
uv run validate_memory_bank.py /path/to/project
uv run validate_memory_bank.py /path/to/project --fix
```

### Process Current Session (6 R's Pipeline)

```bash
# 1. REDUCE — Extract insights from SESSION.md
uv run reduce_sessions.py /path/to/project

# 2. REFLECT — Find connections to existing plans
uv run reflect.py /path/to/project --focus "current milestone"

# 3. REWEAVE — Backward-link insights to archive
uv run reweave.py /path/to/project --new-insight "Lesson from session"

# 4. RETHINK — Challenge assumptions
uv run rethink.py /path/to/project --challenge-area "decision point"
```

### Archive Old Sessions

```bash
uv run archive_sessions.py /path/to/project --threshold 20 --keep 10
```

### Sync Current State (pre-compact)

```bash
uv run sync_context.py /path/to/project --task "Current task" --pending "Item 1,Item 2"
```

### Obsidian Setup (v1.0.0)

1. Copy `templates.obsidian/` files to your Obsidian vault
2. Enable Dataview plugin in Obsidian settings
3. Navigate to `memory-bank/Obsidian-Structure.md` — central dashboard
4. Use embedded Dataview queries for cross-referencing
5. Set up daily notes to reference cascade structure

**Quick Reference:**
- 📊 Dashboard: `Obsidian-Structure.md` — Start here
- 📋 Three-Space Navigation: `maps/` directory (meta.md, knowledge.md, operations.md)
- 🔍 Graph View: Tag all files with schema frontmatter for connectivity
- 📅 Cascade: Update `master-plan.md` to link to daily logs

---

## Read Order (Mandatory on-init)

Always read memory bank files in this order:

1. `memory-bank/projectbrief.md` — Goals, constraints, stakeholders, lessons `[ALWAYS]`
2. `memory-bank/activeContext.md` — Current focus, blockers, recovery instructions `[SESSION]`
3. `memory-bank/SESSION.md` — Session index (links to daily logs) `[SESSION]`
4. `memory-bank/master-plan.md` — Milestones and upcoming work `[ALWAYS]`

> `[ALWAYS]` = load in every context. `[SESSION]` = load during active work sessions.  
> `logs/`, `archive/`, `plans/` are `[SEARCH]` scope — never auto-loaded; access on demand.

---

## Lifecycle Hooks

Three standard lifecycle events govern all memory operations.

### `on-init` — Session Start

**Trigger:** Agent begins a new session or loads memory bank.

**Actions (in order):**
1. Read memory bank files in read order above
2. Check SESSION.md index row count:
   - **>20 entries** → move oldest entries to `archive/sessions-YYYY.md`, keep last 10
   - **>10 entries without distillation** → flag `⚠️ SESSION.md has N entries. Consider distilling key lessons. (last distilled: YYYY-MM-DD)`
3. Load `activeContext.md` Recovery Instructions and resume from last known state

### `on-end` — Session End

**Trigger:** Agent completes work or user ends session.

**Actions (in order):**
1. Flush current state to `activeContext.md` (update all 4 named blocks: Agent Context, Current Task, Pending, Recovery Instructions)
2. Append summary row to `SESSION.md` index: `| Date | Version | Summary | Log Link |`
3. Write full session detail to `logs/YYYY-MM-DD.md`
4. **Knowledge distillation:** Extract 1–3 key lessons. Tag each as `[P0][LESSON]` (permanent) or `[P1][LESSON][expires:YYYY-MM-DD]` (90-day). Propose for `projectbrief.md`. User confirms Y/N.
5. Update `master-plan.md` if milestones changed

### `pre-compact` — Before Context Compression ⚠️ HARD RULE

**Trigger:** Conversation exceeds ~30 exchanges, or context pressure detected.

**Actions (not optional):**
1. Immediately flush working state to `activeContext.md`:
   - `## Current Task` — what's being worked on right now
   - `## Pending` — checklist of remaining items
   - `## Recovery Instructions` — what to do first when reloading
2. Append a checkpoint entry to `SESSION.md` if significant progress has been made
3. Continue work after flush completes

---

## Priority Tags

Every memory entry SHOULD have a priority tag. Priority determines retention and archiving behavior.

| Tag | Meaning | Retention |
|-----|---------|-----------|
| `[P0]` | Permanent — core knowledge, never archive | Forever |
| `[P1]` | Important — archive after 90 days if unused | 90 days |
| `[P2]` | Temporary — archive after 30 days | 30 days |

Optional metadata fields: `expires:YYYY-MM-DD`, `review:YYYY-MM-DD`

> See `references/tag-system.md` for complete documentation including type tags (DEC/FACT/PREF/LESSON) and sensitivity markers.

---

## Type Tags

Use alongside priority tags for categorization and selective loading:

| Tag | Name | When to Use |
|-----|------|-------------|
| `[DEC]` | Decision | Recording a choice between alternatives with rationale |
| `[FACT]` | Fact | Verified technical facts, measurements, specifications |
| `[PREF]` | Preference | User or project conventions, style choices |
| `[LESSON]` | Lesson | Distilled insights from experience — most valuable type |

**Format:** `[Priority][Type]` → example: `[P1][DEC][expires:2026-05-18] Chose React Query over SWR`

---

## Memory Isolation (3-Scope Model)

| Scope | Files | When Loaded |
|-------|-------|-------------|
| `[ALWAYS]` | `projectbrief.md`, `master-plan.md`, `README.md` | Every session, every agent |
| `[SESSION]` | `activeContext.md`, `SESSION.md` | Active work sessions only |
| `[SEARCH]` | `logs/*`, `archive/*`, `plans/*` | On-demand when agent searches |

---

## Three-Space Conceptual Model

The memory bank's files are organized into three conceptual "spaces" (based on Ars Contexta and Obsidian PKM patterns). This is a **mental model for organization**, not a physical division. The directory remains `memory-bank/` — do not rename folders.

| Space | Role | Files | Example Queries |
|-------|------|-------|-----------------|
| **`self/`** | *Project Identity* — Strategic goals, constraints, vision, core decisions | `projectbrief.md`, `master-plan.md` | "What are our goals?" "When does this ship?" "Why did we choose this tech?" |
| **`notes/`** | *Knowledge Graph* — Living documentation, decisions, lessons, daily work | `SESSION.md`, `activeContext.md`, `logs/`, daily notes | "What did we learn?" "When did we decide this?" "What was blocked?" |
| **`ops/`** | *Operations* — Workflow plans, historical archives, administrative logs | `plans/`, `archive/`, timestamps | "What's the implementation plan?" "Did we try this before?" "When was this archived?" |

**Usage Guidelines:**
- When **designing new MOCs** — structure them around these three spaces
- When **querying in Obsidian** — use backlinks to navigate between spaces
- When **distilling lessons** — move from `notes/` → `self/` (lesson becomes permanent)
- When **archiving** — move from `notes/` → `ops/` (keep self-space forever)
- When **thinking about retention** — `self/` is eternal, `notes/` rotate, `ops/` are historical

---

## Templates

Use templates from `templates/` directory for quick initialization:

| Template | Purpose |
|----------|---------|
| `projectbrief.md` | Goals, constraints, stakeholders |
| `activeContext.md` | 4-block working memory |
| `SESSION.md` | Session index format |
| `master-plan.md` | Milestones structure |
| `daily-log.md` | Daily session format |

---

## File Formats

See `references/file-formats.md` for detailed specifications of each file.

---

## Deduplication Convention

Before appending any entry to `projectbrief.md` or `SESSION.md`:
1. **Check** if a semantically equivalent entry already exists
2. **If found:** Update the existing entry's content and its `review:` date — do not duplicate
3. **If not found:** Append the new entry normally

---

## Archiving Protocol

When `SESSION.md` index exceeds 20 entries:
1. Move the oldest entries to `archive/sessions-YYYY.md` (keep last 10 in SESSION.md)
2. Maintain the same table format in the archive file
3. Add note at top: `Archived from SESSION.md on YYYY-MM-DD`

---

## Sensitivity Marker

Mark sensitive entries with `[PRIVATE]`:
```
[P0][PREF][PRIVATE] Database password rotation occurs every 90 days via Vault
```
- Entries **without** `[PRIVATE]` are treated as shareable by default
- `[PRIVATE]` entries must not appear in shared or multi-agent contexts

---

## Allowed Write Paths

Prompts may only create/modify files under these paths:

| Path | Purpose |
|------|---------|
| `memory-bank/projectbrief.md` | Goals, constraints, stakeholders, lessons |
| `memory-bank/activeContext.md` | Current focus, blockers, notes |
| `memory-bank/SESSION.md` | Summary index of sessions |
| `memory-bank/master-plan.md` | Milestones and roadmap |
| `memory-bank/README.md` | Conventions and usage guide |
| `memory-bank/logs/*.md` | Daily session logs |
| `memory-bank/archive/*.md` | Archived session entries |
| `memory-bank/plans/*.md` | Implementation plans |
