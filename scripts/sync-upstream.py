#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0",
# ]
# [tool.uv]
# exclude-newer = "2026-09-01T00:00:00Z"
# ///
"""
sync-upstream.py

Sync the fork with upstream excalidraw master. The fork carries exactly
one modification — the Dockerfile (collab URL as build arg) — so the
sync is a rebase onto upstream/master, followed by a check that the
Dockerfile is still the only file that differs.

Usage:
    uv run --script scripts/sync-upstream.py check    # fetch + verify diff only
    uv run --script scripts/sync-upstream.py          # fetch + rebase + verify
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import typer
from rich.console import Console

console = Console(stderr=True)

app = typer.Typer(
    name="sync-upstream",
    help="Rebase the fork onto upstream master and verify only the Dockerfile differs.",
    add_completion=True,
    # Note: no no_args_is_help here — the callback is the default command
    # (rebase) and no_args_is_help would shadow it.
)

REPO_ROOT = Path.cwd()
DOCKERFILE = "Dockerfile"


def _git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    console.print(f"[dim]$ git {' '.join(args)}[/dim]")
    return subprocess.run(["git", *args], check=check, text=True, capture_output=True)


def _only_dockerfile_differs() -> bool:
    result = _git(["diff", "--name-only", "upstream/master"], check=False)
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    if changed == [DOCKERFILE]:
        console.print(f"[green]ok: {DOCKERFILE} is the only modified file[/green]")
        return True
    console.print(
        f"[red]unexpected modified files: {', '.join(changed) or '(none)'} "
        f"(expected only {DOCKERFILE})[/red]"
    )
    return False


def _fetch_upstream() -> None:
    _git(["fetch", "upstream", "master"])


@app.command()
def check() -> None:
    """Fetch upstream master and verify only the Dockerfile differs (no rebase)."""
    _fetch_upstream()
    if not _only_dockerfile_differs():
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Fetch upstream master, rebase the fork onto it, verify the diff."""
    if ctx.invoked_subcommand is not None:
        return
    if not (REPO_ROOT / ".git").exists():
        console.print("[red]not a git checkout — run from the fork root[/red]")
        raise typer.Exit(1)
    _fetch_upstream()
    rebase = _git(["rebase", "upstream/master"], check=False)
    if rebase.returncode != 0:
        console.print("[red]rebase failed — resolve conflicts, then re-run check[/red]")
        console.print(rebase.stdout or rebase.stderr)
        raise typer.Exit(1)
    if not _only_dockerfile_differs():
        console.print("[red]rebase applied but the diff changed — investigate[/red]")
        raise typer.Exit(1)
    console.print("[green]fork is up to date with upstream/master[/green]")


if __name__ == "__main__":
    app()
