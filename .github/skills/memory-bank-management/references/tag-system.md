# Tag System Reference

Memory entries use a combination of priority tags and type tags for categorization and lifecycle management.

---

## Priority Tags

Every memory entry SHOULD have a priority tag. Priority determines retention and archiving behavior.

| Tag | Meaning | Retention | Example |
|-----|---------|-----------|---------|
| `[P0]` | Permanent — core knowledge, never archive | Forever | `[P0][LESSON] Always run tests before committing to main` |
| `[P1]` | Important — archive after 90 days if unused | 90 days | `[P1][DEC][expires:2026-05-18] Chose PostgreSQL over MySQL for JSON support` |
| `[P2]` | Temporary — archive after 30 days | 30 days | `[P2][FACT][expires:2026-03-20] Current API rate limit is 1000 req/min` |

### Priority Guidelines

- **Use `[P0]` for:** Core project knowledge, permanent conventions, critical lessons
- **Use `[P1]` for:** Important decisions, significant facts, time-sensitive information
- **Use `[P2]` for:** Temporary facts, current measurements, short-term context

---

## Type Tags

Use alongside priority tags for categorization and selective loading.

| Tag | Name | When to Use | Examples |
|-----|------|-------------|----------|
| `[DEC]` | **Decision** | Recording a choice between alternatives with rationale | `[P1][DEC] Chose FastAPI over Flask for async support and auto-docs` |
| `[FACT]` | **Fact** | Verified technical facts, measurements, specifications | `[P2][FACT] PostgreSQL max connections default is 100` |
| `[PREF]` | **Preference** | User or project preferences, conventions, style choices | `[P0][PREF] Use 2-space indentation for all TypeScript files` |
| `[LESSON]` | **Lesson** | Distilled insights from experience — the most valuable type | `[P0][LESSON] Always check SESSION.md for context before starting new work` |

### Type Guidelines

- **Start with `[LESSON]`** — it's the most valuable type for knowledge distillation
- **Use `[DEC]` when recording tradeoffs** — always include rationale
- **Use `[FACT]` for measurements and specs** — these tend to expire, so use P1/P2
- **Use `[PREF]` for conventions** — these tend to be permanent (P0)

---

## Metadata Fields

Optional inline metadata fields provide additional lifecycle information.

| Field | Format | Purpose |
|-------|--------|---------|
| `expires:YYYY-MM-DD` | After priority tag | When to consider archiving this entry |
| `review:YYYY-MM-DD` | After priority tag | When to review this entry for relevance |

### Example with Full Metadata

```markdown
[P1][DEC][expires:2026-05-18][review:2026-04-01] Chose React Query over SWR for cache invalidation features
```

---

## Combining Tags

Format: `[Priority][Type]` optionally followed by metadata.

### Examples

```markdown
[P0][LESSON] Memory bank must be read in order: projectbrief → activeContext → SESSION → master-plan
[P1][DEC][expires:2026-05-18] Selected Poetry over pip for dependency management
[P2][FACT][expires:2026-03-20] Build takes ~4 minutes on CI; ~2 minutes locally
[P0][PREF] All commit messages must follow Conventional Commits format
[P1][LESSON][review:2026-04-01] Parallel subagent calls are 3x faster than sequential for independent tasks
```

---

## Sensitivity Marker

Mark sensitive entries with `[PRIVATE]`:

```markdown
[P0][PREF][PRIVATE] Database password rotation occurs every 90 days via Vault
```

- Entries **without** `[PRIVATE]` are treated as shareable by default
- `[PRIVATE]` entries must not appear in shared or multi-agent contexts
- Scopes handle **loading**; `[PRIVATE]` handles **content filtering**

---

## Tag Usage Summary

| Priority | Type | Use Case |
|----------|------|----------|
| `[P0]` | `[LESSON]` | Permanent lessons learned |
| `[P0]` | `[PREF]` | Project conventions |
| `[P1]` | `[DEC]` | Important decisions with rationale |
| `[P1]` | `[LESSON]` | Time-sensitive lessons |
| `[P2]` | `[FACT]` | Temporary facts and measurements |
| `[P2]` | `[DEC]` | Temporary decisions |
