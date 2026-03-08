#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0", "typer>=0.9.0"]
# ///
"""
Extract lessons from session logs for knowledge distillation.

Usage:
    uv run distill_lessons.py [PATH] [--output projectbrief.md]

Examples:
    uv run distill_lessons.py                           # Extract lessons from logs
    uv run distill_lessons.py . --dry-run               # Preview without changes
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Extract lessons from session logs for knowledge distillation")
console = Console()

# Pattern to match lessons in logs
LESSON_PATTERN = re.compile(
    r"\[(P[012])\]\[LESSON\](?:\[expires:(\d{4}-\d{2}-\d{2})\])?\s*(.+?)(?=\n|$)",
    re.MULTILINE,
)


@app.command()
def distill(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project root (default: current directory)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for lessons (default: print to console)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be added without making changes",
    ),
) -> None:
    """Extract lessons from session logs for knowledge distillation."""
    target = (path or Path.cwd()).resolve()
    memory_bank = target / "memory-bank"
    logs_dir = memory_bank / "logs"

    if not logs_dir.exists():
        console.print(f"[red]Error:[/red] logs directory not found at {logs_dir}")
        raise typer.Exit(1)

    # Find all log files
    log_files = sorted(logs_dir.glob("*.md"), key=lambda p: p.name, reverse=True)

    if not log_files:
        console.print("[yellow]No log files found in logs/[/yellow]")
        return

    # Extract lessons from each log
    all_lessons = []

    for log_file in log_files:
        content = log_file.read_text(encoding="utf-8")
        for match in LESSON_PATTERN.finditer(content):
            priority = match.group(1)
            expires = match.group(2)
            description = match.group(3).strip()
            all_lessons.append({
                "priority": priority,
                "expires": expires,
                "description": description,
                "source": log_file.name,
            })

    if not all_lessons:
        console.print("[yellow]No lessons found in logs[/yellow]")
        return

    # Print summary
    table = Table(title=f"Lessons Found ({len(all_lessons)})")
    table.add_column("Priority", style="cyan")
    table.add_column("Expires", style="yellow")
    table.add_column("Description", style="green")
    table.add_column("Source", style="dim")

    for lesson in all_lessons:
        table.add_row(
            lesson["priority"],
            lesson["expires"] or "Never",
            lesson["description"][:60] + ("..." if len(lesson["description"]) > 60 else ""),
            lesson["source"],
        )

    console.print(table)

    # Output to file if specified
    if output:
        output_path = (output if output.is_absolute() else target / output).resolve()

        if dry_run:
            console.print(f"\n[yellow]DRY RUN[/yellow] Would append {len(all_lessons)} lessons to: {output_path}")
            return

        # Read existing content
        if output_path.exists():
            existing = output_path.read_text(encoding="utf-8")
        else:
            existing = ""

        # Format lessons
        lessons_text = "\n".join(
            f"- [{l['priority']}][LESSON]{'[expires:' + l['expires'] + ']' if l['expires'] else ''} {l['description']}"
            for l in all_lessons
        )

        # Append to Lessons Learned section or create it
        if "## Lessons Learned" in existing:
            # Find the section and append
            lines = existing.split("\n")
            new_lines = []
            in_lessons = False

            for line in lines:
                new_lines.append(line)
                if line.strip() == "## Lessons Learned":
                    in_lessons = True
                    new_lines.append(lessons_text)
                elif line.startswith("## ") and in_lessons:
                    in_lessons = False

            output_path.write_text("\n".join(new_lines), encoding="utf-8")
        else:
            # Add section at the end
            output_path.write_text(
                existing + f"\n\n## Lessons Learned\n{lessons_text}\n",
                encoding="utf-8",
            )

        console.print(f"\n[green]✅ Appended {len(all_lessons)} lessons to:[/green] {output_path}")


if __name__ == "__main__":
    app()
