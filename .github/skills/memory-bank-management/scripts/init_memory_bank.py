#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0", "typer>=0.9.0"]
# ///
"""
Initialize a new memory bank from templates.

Usage:
    uv run init_memory_bank.py [PATH] [--force]

Examples:
    uv run init_memory_bank.py                           # Initialize in current directory
    uv run init_memory_bank.py /path/to/project          # Initialize in specific project
    uv run init_memory_bank.py . --force                 # Overwrite existing files
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Initialize a new memory bank from templates")
console = Console()

# Template content for each file
TEMPLATES = {
    "projectbrief.md": """# Project Brief

## Goal
[What is the primary objective of this project?]

## Constraints
- Platform: [e.g., VS Code + GitHub Copilot, Node.js, Python]
- Frameworks: [e.g., React, FastAPI, Next.js]
- Dependencies: [Key libraries or tools]

## Stakeholders
- [Who uses or maintains this project?]

## Definition of Done
- [ ] [Criterion 1: e.g., All tests pass]
- [ ] [Criterion 2: e.g., Documentation complete]
- [ ] [Criterion 3: e.g., Code reviewed]

---
## Lessons Learned
<!-- Append lessons here with format: [P0][LESSON] Description -->

---
*Created: {date} | Last Updated: {date}*
""",
    "activeContext.md": """# Active Context

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
*Last Updated: {date}*
""",
    "SESSION.md": """# Session Log

## {date} — v0.1.0
**Objective:** Initialize memory bank

**Actions:**
- Created memory-bank directory structure
- Initialized core files from templates

**Status:** ✅ Complete

---
""",
    "master-plan.md": """# Master Plan

## Milestones
1. [ ] **Phase 1: [Name]** — [Description]

## Upcoming Work
- [ ] [Next immediate task]

## Completed
- [x] Memory bank initialized

---
*Last Updated: {date}*
""",
    "README.md": """# Memory Bank

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
*Created: {date}*
""",
}

REQUIRED_DIRS = ["logs", "archive", "plans"]


@app.command()
def init(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project root (default: current directory)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be created without making changes",
    ),
) -> None:
    """Initialize a new memory bank in the specified directory."""
    from datetime import datetime

    target = (path or Path.cwd()).resolve()
    memory_bank = target / "memory-bank"

    if dry_run:
        console.print(f"[yellow]DRY RUN[/yellow] Would initialize memory bank at: {memory_bank}")
        return

    # Check if memory bank already exists
    if memory_bank.exists() and not force:
        existing_files = list(memory_bank.glob("*.md"))
        if existing_files:
            console.print(f"[red]Error:[/red] Memory bank already exists at {memory_bank}")
            console.print("Use --force to overwrite existing files")
            raise typer.Exit(1)

    # Create memory-bank directory
    memory_bank.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    for dir_name in REQUIRED_DIRS:
        (memory_bank / dir_name).mkdir(exist_ok=True)

    # Create files from templates
    date_str = datetime.now().strftime("%Y-%m-%d")
    created_files = []

    for filename, template in TEMPLATES.items():
        file_path = memory_bank / filename
        content = template.format(date=date_str)

        if file_path.exists() and not force:
            console.print(f"[yellow]Skipping:[/yellow] {filename} (already exists)")
            continue

        file_path.write_text(content, encoding="utf-8")
        created_files.append(filename)

    # Print summary
    table = Table(title="Memory Bank Initialized")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")

    for filename in TEMPLATES:
        status = "✅ Created" if filename in created_files else "⏭️ Skipped"
        table.add_row(filename, status)

    for dir_name in REQUIRED_DIRS:
        table.add_row(f"{dir_name}/", "📁 Created")

    console.print(table)
    console.print(f"\n[green]✅ Memory bank initialized at:[/green] {memory_bank}")


if __name__ == "__main__":
    app()
