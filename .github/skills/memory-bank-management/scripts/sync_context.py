#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0", "typer>=0.9.0"]
# ///
"""
Flush current state to activeContext.md (pre-compact hook).

Usage:
    uv run sync_context.py [PATH] [--task "Current task"] [--pending "Item 1,Item 2"]

Examples:
    uv run sync_context.py                                    # Interactive mode
    uv run sync_context.py . --task "Implementing feature X"  # Set current task
    uv run sync_context.py . --pending "Fix bug,Write tests"  # Set pending items
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="Flush current state to activeContext.md")
console = Console()


@app.command()
def sync(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project root (default: current directory)",
    ),
    task: Optional[str] = typer.Option(
        None,
        "--task",
        "-t",
        help="Current task description",
    ),
    pending: Optional[str] = typer.Option(
        None,
        "--pending",
        "-p",
        help="Comma-separated list of pending items",
    ),
    agent_context: Optional[str] = typer.Option(
        None,
        "--context",
        "-c",
        help="Agent context information",
    ),
    recovery: Optional[str] = typer.Option(
        None,
        "--recovery",
        "-r",
        help="Recovery instructions",
    ),
) -> None:
    """Flush current state to activeContext.md."""
    target = (path or Path.cwd()).resolve()
    memory_bank = target / "memory-bank"
    active_context = memory_bank / "activeContext.md"

    if not active_context.exists():
        console.print(f"[red]Error:[/red] activeContext.md not found at {active_context}")
        raise typer.Exit(1)

    # Read existing content
    content = active_context.read_text(encoding="utf-8")

    # Update sections if provided
    if task:
        content = update_section(content, "## Current Task", task)

    if pending:
        items = [f"- [ ] {item.strip()}" for item in pending.split(",")]
        content = update_section(content, "## Pending", "\n".join(items))

    if agent_context:
        content = update_section(content, "## Agent Context", agent_context)

    if recovery:
        content = update_section(content, "## Recovery Instructions", recovery)

    # Update timestamp
    date_str = datetime.now().strftime("%Y-%m-%d")
    if "*Last Updated:" in content:
        import re

        content = re.sub(
            r"\*Last Updated:.*\*",
            f"*Last Updated: {date_str}*",
            content,
        )
    else:
        content += f"\n---\n*Last Updated: {date_str}*"

    # Write back
    active_context.write_text(content, encoding="utf-8")
    console.print(f"[green]✅ Synced state to:[/green] {active_context}")


def update_section(content: str, section_header: str, new_content: str) -> str:
    """Update a section in the content."""
    lines = content.split("\n")
    new_lines = []
    in_section = False
    section_found = False

    for i, line in enumerate(lines):
        if line.strip() == section_header:
            in_section = True
            section_found = True
            new_lines.append(line)
            new_lines.append(new_content)
            continue

        if in_section:
            # Skip until next section or end
            if line.startswith("## ") or line.startswith("---"):
                in_section = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    # If section not found, add it
    if not section_found:
        new_lines.append(f"\n{section_header}")
        new_lines.append(new_content)

    return "\n".join(new_lines)


if __name__ == "__main__":
    app()
