# Lifecycle Hooks Reference

Lifecycle hooks are standard events that govern memory operations. All prompts should reference these hooks.

---

## `on-init` — Session Start

**Trigger:** Agent begins a new session or loads memory bank.

**Actions (in order):**
1. Read memory bank files in read order: `projectbrief.md` → `activeContext.md` → `SESSION.md` → `master-plan.md`
2. Check SESSION.md index row count:
   - **>20 entries** → move oldest entries to `archive/sessions-YYYY.md`, keep last 10
   - **>10 entries without distillation** → flag `⚠️ SESSION.md has N entries. Consider distilling key lessons. (last distilled: YYYY-MM-DD)`
3. Load `activeContext.md` Recovery Instructions and resume from last known state

### Example Implementation

```python
# Using the scripts
uv run validate_memory_bank.py
uv run archive_sessions.py --dry-run  # Check first
uv run archive_sessions.py            # Execute if needed
```

---

## `on-end` — Session End

**Trigger:** Agent completes work or user ends session.

**Actions (in order):**
1. Flush current state to `activeContext.md` (update all 4 named blocks: Agent Context, Current Task, Pending, Recovery Instructions)
2. Append summary row to `SESSION.md` index: `| Date | Version | Summary | Log Link |`
3. Write full session detail to `logs/YYYY-MM-DD.md`
4. **Knowledge distillation:** Extract 1–3 key lessons. Tag each as `[P0][LESSON]` (permanent) or `[P1][LESSON][expires:YYYY-MM-DD]` (90-day). Propose for `projectbrief.md`. User confirms Y/N.
5. Update `master-plan.md` if milestones changed

### Example Implementation

```python
# Sync state before ending
uv run sync_context.py . --task "Completed feature X" --pending "Write tests,Update docs"

# Distill lessons from logs
uv run distill_lessons.py --dry-run
uv run distill_lessons.py --output projectbrief.md
```

---

## `pre-compact` — Before Context Compression ⚠️ HARD RULE

**Trigger:** Conversation exceeds ~30 exchanges, or context pressure detected.

**Actions (not optional):**
1. Immediately flush working state to `activeContext.md`:
   - `## Current Task` — what's being worked on right now
   - `## Pending` — checklist of remaining items
   - `## Recovery Instructions` — what to do first when reloading
2. Append a checkpoint entry to `SESSION.md` if significant progress has been made
3. Continue work after flush completes

### Example Implementation

```python
# Flush state immediately
uv run sync_context.py . --task "Mid-task: implementing X" --pending "Step 3,Step 4,Step 5" --recovery "Resume from Step 3"
```

---

## Hook Summary Table

| Hook | Trigger | Primary Action | Script |
|------|---------|----------------|--------|
| `on-init` | Session start | Read memory bank, check archiving | `validate_memory_bank.py`, `archive_sessions.py` |
| `on-end` | Session end | Flush state, distill lessons | `sync_context.py`, `distill_lessons.py` |
| `pre-compact` | Context pressure | Flush state immediately | `sync_context.py` |

---

## Automation with Scripts

All lifecycle operations can be automated using the provided Python scripts:

```bash
# Initialize a new memory bank
uv run init_memory_bank.py /path/to/project

# Validate memory bank state
uv run validate_memory_bank.py /path/to/project

# Archive old sessions
uv run archive_sessions.py /path/to/project --threshold 20 --keep 10

# Sync current state
uv run sync_context.py /path/to/project --task "Current task"

# Distill lessons from logs
uv run distill_lessons.py /path/to/project --output projectbrief.md
```

All scripts support `--dry-run` to preview changes without executing.
