# Building Better Skills: Lessons from Claude's Official Guide

This document distills key insights from `claude-skill.md` into actionable lessons for improving skill development.

---

## Lesson 1: The Progressive Disclosure Principle

**Problem**: Loading all skill content into context wastes tokens and degrades performance.

**Solution**: Use the 3-level system:

| Level | Content | When Loaded |
|-------|---------|-------------|
| 1 | YAML frontmatter | Always (system prompt) |
| 2 | SKILL.md body | When skill is relevant |
| 3 | references/* | On-demand navigation |

**Action**: Keep SKILL.md under 5,000 words. Move detailed docs to `references/`.

---

## Lesson 2: The Description Field is Critical

**Problem**: Skills don't trigger when they should, or trigger too often.

**Good structure**:
```yaml
description: Analyzes Figma design files and generates 
developer handoff documentation. Use when user uploads 
.fig files, asks for "design specs", "component 
documentation", or "design-to-code handoff".
```

**Must include**:
- ✅ What the skill does
- ✅ When to use it (trigger conditions)
- ✅ Specific phrases users would say
- ✅ File types if relevant

**Avoid**:
- ❌ Generic descriptions ("Helps with projects")
- ❌ Missing trigger conditions
- ❌ XML tags (< >)

---

## Lesson 3: Effective Skill Structure

```
skill-name/
├── SKILL.md              # Required - main instructions
├── scripts/              # Optional - executable code
│   └── *.py, *.sh
├── references/          # Optional - detailed docs
│   └── *.md
└── assets/              # Optional - templates
    └── *.md
```

**Critical Rules**:
- SKILL.md must be exact (case-sensitive)
- Folder name: kebab-case only (e.g., `my-skill` ✅, `MySkill` ❌)
- No README.md inside skill folder
- All docs in SKILL.md or references/

---

## Lesson 4: Write Actionable Instructions

**Bad**:
> Validate the data before proceeding.

**Good**:
> Run `python scripts/validate.py --input {filename}` to check data format.
> If validation fails, common issues include:
> - Missing required fields (add them to the CSV)
> - Invalid date formats (use YYYY-MM-DD)

**Tips**:
- Be specific and actionable
- Include expected output
- Add error handling guidance
- Use bullet points and numbered lists

---

## Lesson 5: Test Triggering, Not Just Functionality

**Three testing areas**:

| Test Type | Goal | Method |
|-----------|------|--------|
| Triggering | Loads at right times | Run 10-20 test queries |
| Functional | Produces correct outputs | Compare expected vs actual |
| Performance | Improves vs baseline | Count tokens, API calls |

**Trigger test examples**:
```markdown
Should trigger:
- "Help me set up a new workspace"
- "I need to create a project"
- "Initialize for Q4 planning"

Should NOT trigger:
- "What's the weather?"
- "Help me write Python code"
```

---

## Lesson 6: Common Troubleshooting Patterns

| Symptom | Cause | Fix |
|---------|-------|-----|
| Skill won't upload | Wrong filename | Must be exactly SKILL.md |
| Invalid frontmatter | YAML formatting | Check quotes, delimiters |
| Skill doesn't trigger | Vague description | Add trigger phrases |
| Skill triggers too often | Too generic | Add negative triggers |
| Instructions not followed | Buried/verbose | Put critical info at top |

---

## Lesson 7: Patterns That Work

### Pattern 1: Sequential Workflow
```
Step 1: Call MCP tool X
Step 2: Wait for Y
Step 3: Call MCP tool Z
```

### Pattern 2: Multi-MCP Coordination
- Phase 1: Design (Figma MCP)
- Phase 2: Storage (Drive MCP)
- Phase 3: Tasks (Linear MCP)

### Pattern 3: Iterative Refinement
1. Generate draft
2. Validate quality
3. Refine issues
4. Repeat until threshold met

---

## Lesson 8: Avoid These Mistakes

1. **No README in skill folder** — Use SKILL.md or references/
2. **Name with spaces/capitals** — Use kebab-case
3. **Missing trigger conditions** — Always include "Use when..."
4. **Instructions buried in text** — Use headers, bullets, code blocks
5. **No error handling** — Include troubleshooting section

---

## Quick Checklist Before Upload

- [ ] Folder named in kebab-case
- [ ] SKILL.md exists (exact spelling)
- [ ] YAML frontmatter has --- delimiters
- [ ] name field: kebab-case
- [ ] description includes WHAT + WHEN
- [ ] No XML tags anywhere
- [ ] Instructions are clear and actionable
- [ ] Error handling included
- [ ] Examples provided
- [ ] Tested triggering works correctly

---

## References

- Official Guide: `claude-skill.md`
- skill-creator skill: Use for generating/reviewing skills
- GitHub: anthropics/skills (example skills)
