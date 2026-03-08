#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0", "typer>=0.9.0"]
# ///
"""
Validate memory bank state and integrity.

Usage:
    uv run validate_memory_bank.py [PATH] [--fix]

Examples:
    uv run validate_memory_bank.py                        # Validate current directory
    uv run validate_memory_bank.py /path/to/project       # Validate specific project
    uv run validate_memory_bank.py . --fix                # Auto-fix issues
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Validate memory bank state and integrity")
console = Console()

# Required files and their expected sections
REQUIRED_FILES = {
    "projectbrief.md": ["# Project Brief", "## Goal", "## Constraints"],
    "activeContext.md": ["# Active Context", "## Agent Context", "## Current Task", "## Pending", "## Recovery Instructions"],
    "SESSION.md": ["# Session Log"],
    "master-plan.md": ["# Master Plan", "## Milestones"],
    "README.md": ["# Memory Bank"],
}

REQUIRED_DIRS = ["logs", "archive", "plans"]


@app.command()
def validate(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project root (default: current directory)",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix issues where possible",
    ),
) -> None:
    """Validate memory bank structure and content."""
    from datetime import datetime

    target = (path or Path.cwd()).resolve()
    memory_bank = target / "memory-bank"

    results = []

    # Check memory-bank directory exists
    if not memory_bank.exists():
        results.append(("memory-bank/", "❌ Missing", "Directory not found"))
        if fix:
            memory_bank.mkdir(parents=True)
            results[-1] = ("memory-bank/", "✅ Created", "Directory created")
    else:
        results.append(("memory-bank/", "✅ Exists", ""))

    # Check required directories
    for dir_name in REQUIRED_DIRS:
        dir_path = memory_bank / dir_name
        if not dir_path.exists():
            results.append((f"{dir_name}/", "❌ Missing", "Directory not found"))
            if fix:
                dir_path.mkdir(parents=True, exist_ok=True)
                results[-1] = (f"{dir_name}/", "✅ Created", "Directory created")
        else:
            results.append((f"{dir_name}/", "✅ Exists", ""))

    # Check required files
    for filename, required_sections in REQUIRED_FILES.items():
        file_path = memory_bank / filename

        if not file_path.exists():
            results.append((filename, "❌ Missing", "File not found"))
            continue

        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for required sections
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            if missing_sections:
                results.append(
                    (filename, "⚠️ Incomplete", f"Missing: {', '.join(missing_sections)}")
                )
            else:
                results.append((filename, "✅ Valid", ""))

        except Exception as e:
            results.append((filename, "❌ Error", str(e)))

    # Check SESSION.md has entry for today
    session_file = memory_bank / "SESSION.md"
    if session_file.exists():
        today = datetime.now().strftime("%Y-%m-%d")
        content = session_file.read_text(encoding="utf-8")
        if today in content:
            results.append(("SESSION.md (today)", "✅ Has entry", today))
        else:
            results.append(("SESSION.md (today)", "⚠️ No entry", f"No entry for {today}"))

    # Print results
    table = Table(title="Memory Bank Validation")
    table.add_column("Item", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    for item, status, details in results:
        table.add_row(item, status, details)

    console.print(table)

    # Summary
    errors = sum(1 for _, s, _ in results if s.startswith("❌"))
    warnings = sum(1 for _, s, _ in results if s.startswith("⚠️"))

    if errors == 0 and warnings == 0:
        console.print("\n[green]✅ Memory bank is valid[/green]")
    elif errors > 0:
        console.print(f"\n[red]❌ Found {errors} error(s), {warnings} warning(s)[/red]")
        if not fix:
            console.print("[yellow]Run with --fix to auto-fix issues[/yellow]")
        raise typer.Exit(1)
    else:
        console.print(f"\n[yellow]⚠️ Found {warnings} warning(s)[/yellow]")


if __name__ == "__main__":
    app()
