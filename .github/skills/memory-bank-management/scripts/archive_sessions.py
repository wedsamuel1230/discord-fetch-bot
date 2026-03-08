#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0", "typer>=0.9.0"]
# ///
"""
Archive old SESSION.md entries when the index exceeds threshold.

Usage:
    uv run archive_sessions.py [PATH] [--threshold 20] [--keep 10]

Examples:
    uv run archive_sessions.py                           # Archive if >20 entries
    uv run archive_sessions.py . --threshold 15          # Custom threshold
    uv run archive_sessions.py . --dry-run               # Preview without changes
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Archive old SESSION.md entries")
console = Console()

# Pattern to match session entries in SESSION.md
SESSION_ENTRY_PATTERN = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2})\s+[—-]\s+v[\d.]+",
    re.MULTILINE,
)


def parse_session_entries(content: str) -> list[tuple[int, str, str]]:
    """Parse SESSION.md and return list of (start_pos, date, full_entry)."""
    entries = []
    for match in SESSION_ENTRY_PATTERN.finditer(content):
        entries.append((match.start(), match.group(1), match.group(0)))
    return entries


@app.command()
def archive(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project root (default: current directory)",
    ),
    threshold: int = typer.Option(
        20,
        "--threshold",
        "-t",
        help="Archive when entries exceed this number",
    ),
    keep: int = typer.Option(
        10,
        "--keep",
        "-k",
        help="Number of recent entries to keep in SESSION.md",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be archived without making changes",
    ),
) -> None:
    """Archive old SESSION.md entries to archive/sessions-YYYY.md."""
    target = (path or Path.cwd()).resolve()
    memory_bank = target / "memory-bank"
    session_file = memory_bank / "SESSION.md"
    archive_dir = memory_bank / "archive"

    if not session_file.exists():
        console.print(f"[red]Error:[/red] SESSION.md not found at {session_file}")
        raise typer.Exit(1)

    content = session_file.read_text(encoding="utf-8")
    entries = parse_session_entries(content)

    if len(entries) <= threshold:
        console.print(
            f"[green]✅ No archiving needed:[/green] "
            f"{len(entries)} entries (threshold: {threshold})"
        )
        return

    # Determine which entries to archive
    entries_to_archive = entries[:-keep]  # All but the last 'keep' entries
    entries_to_keep = entries[-keep:]  # The last 'keep' entries

    if dry_run:
        console.print(f"[yellow]DRY RUN[/yellow] Would archive {len(entries_to_archive)} entries")
        table = Table(title="Entries to Archive")
        table.add_column("Date", style="cyan")
        for _, date, _ in entries_to_archive:
            table.add_row(date)
        console.print(table)
        return

    # Create archive directory if needed
    archive_dir.mkdir(exist_ok=True)

    # Extract content for each entry
    lines = content.split("\n")
    archive_content = []
    keep_content = []

    # Find the header (everything before first entry)
    first_entry_pos = entries[0][0]
    header = content[:first_entry_pos]

    # Build archive content
    for i, (pos, date, _) in enumerate(entries_to_archive):
        # Find end of this entry (start of next entry or end of file)
        if i + 1 < len(entries):
            end_pos = entries[i + 1][0]
        else:
            end_pos = len(content)
        archive_content.append(content[pos:end_pos].strip())

    # Build keep content
    for i, (pos, date, _) in enumerate(entries_to_keep):
        if i + 1 < len(entries):
            end_pos = entries[i + 1][0]
        else:
            end_pos = len(content)
        keep_content.append(content[pos:end_pos].strip())

    # Write archive file
    year = datetime.now().year
    archive_file = archive_dir / f"sessions-{year}.md"
    archive_header = f"# Archived Sessions ({year})\n\nArchived from SESSION.md on {datetime.now().strftime('%Y-%m-%d')}\n\n---\n\n"

    if archive_file.exists():
        existing = archive_file.read_text(encoding="utf-8")
        archive_file.write_text(
            existing + "\n\n" + "\n\n".join(archive_content),
            encoding="utf-8",
        )
    else:
        archive_file.write_text(
            archive_header + "\n\n".join(archive_content),
            encoding="utf-8",
        )

    # Update SESSION.md
    new_session_content = header + "\n\n".join(keep_content) + "\n"
    session_file.write_text(new_session_content, encoding="utf-8")

    # Print summary
    console.print(f"[green]✅ Archived {len(entries_to_archive)} entries to:[/green] {archive_file}")
    console.print(f"[green]✅ Kept {len(entries_to_keep)} recent entries in SESSION.md[/green]")


if __name__ == "__main__":
    app()
