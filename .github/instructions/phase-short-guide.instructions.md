---
description: "Use when creating or updating phased initialization/request prompts. Enforces a concise 0-6 phase flow with verification, audit, and actionable next steps."
name: "Short Phase Workflow Guide"
applyTo: ".github/prompts/*.prompt.md"
---

# Short Phase Guide

- **Phase 0 (Recon):** Scan workspace and memory bank, then produce a short initialization digest.
- **Phase 1 (Input):** Capture goal, constraints, stakeholders, and DoD; fill missing details with safe defaults.
- **Phase 1.5 (Ideation):** Propose at least 5 practical environment improvements with impact.
- **Phase 2 (Execution):** Implement planned changes, keep memory bank tracked, and sync session notes.
- **Phase 3 (Verify):** Run checks (memory files, integrity, gitignore, session date, skills dir) and auto-fix once.
- **Phase 4 (Audit):** Perform zero-trust self-audit; resolve any failed audit item before reporting.
- **Phase 5 (Report):** Produce final session report with verdict and evidence.
- **Phase 6 (Next Steps):** Review project brief, update blockers in active context, and start next implementation via subagent.

## Enforcement Notes

- Keep phase instructions concise and execution-oriented.
- Preserve sequence integrity (0 → 1 → 1.5 → 2 → 3 → 4 → 5 → 6).
- Do not claim completion before verification and audit phases are explicitly satisfied.
