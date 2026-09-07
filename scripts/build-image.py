#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0",
#   "pydantic>=2.7",
#   "ruamel.yaml>=0.18",
# ]
# [tool.uv]
# exclude-newer = "2026-09-01T00:00:00Z"
# ///
"""
build-image.py

Build the self-hosted Excalidraw client image (excalidraw:fork-collab)
from config/images.yaml. The collab server URL is baked in at build
time via the VITE_APP_WS_SERVER_URL build arg (the upstream image
hardcodes Excalidraw's public server instead).

Usage:
    uv run --script scripts/build-image.py            # build
    uv run --script scripts/build-image.py --no-cache # build, no cache
    uv run --script scripts/build-image.py --check    # build + verify baked URL

Environment variables:
    EXCALIDRAW_IMAGES_CONFIG  Config file path override (default: config/images.yaml)
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

import typer
from pydantic import BaseModel, Field
from rich.console import Console
from ruamel.yaml import YAML

_ENV_CONFIG = "EXCALIDRAW_IMAGES_CONFIG"
_DEFAULT_CONFIG = Path("config/images.yaml")

console = Console(stderr=True)

app = typer.Typer(
    name="build-image",
    help="Build the excalidraw:fork-collab client image from config/images.yaml.",
    add_completion=True,
    no_args_is_help=True,
)


class BuildArgs(BaseModel):
    VITE_APP_WS_SERVER_URL: str


class ClientSource(BaseModel):
    upstream: str
    fork: str
    upstream_commit: str
    fork_commit: str


class ClientConfig(BaseModel):
    tag: str
    source: ClientSource
    build_args: BuildArgs
    port: int


class RoomConfig(BaseModel):
    image: str
    port: int
    env: dict[str, str]


class DeploymentConfig(BaseModel):
    compose_file: str
    services: list[str]


class ImagesConfig(BaseModel):
    client: ClientConfig
    room: RoomConfig
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)


def _resolve_config_path(cli: Path | None) -> Path:
    raw: str | Path | None = cli
    if raw is None:
        raw = os.environ.get(_ENV_CONFIG)
    if raw is None:
        return Path.cwd() / _DEFAULT_CONFIG
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p


def _load_config(path: Path) -> ImagesConfig:
    yaml = YAML(typ="safe")
    data = yaml.load(path.read_text(encoding="utf-8"))
    return ImagesConfig.model_validate(data)


def _run(cmd: list[str]) -> None:
    console.print(f"[dim]$ {shlex.join(cmd)}[/dim]")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        console.print(f"[red]command failed with exit code {result.returncode}[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Images config file path.",
        envvar=_ENV_CONFIG, show_default=True,
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="Pass --no-cache to docker build."),
    check: bool = typer.Option(False, "--check", help="Build then verify the baked collab URL."),
) -> None:
    """Build the client image from config/images.yaml."""
    cfg = _load_config(_resolve_config_path(config))
    repo_root = Path.cwd()
    if not (repo_root / "Dockerfile").exists():
        console.print("[red]Dockerfile not found — run this from the fork checkout root.[/red]")
        raise typer.Exit(1)

    args = [a for a in ("--no-cache",) if no_cache]
    cmd = [
        "docker", "build", *args,
        f"--build-arg=VITE_APP_WS_SERVER_URL={cfg.client.build_args.VITE_APP_WS_SERVER_URL}",
        "-t", cfg.client.tag, ".",
    ]
    console.print(f"Building [bold]{cfg.client.tag}[/bold] (commit {cfg.client.source.upstream_commit})")
    _run(cmd)

    if check:
        _verify_baked_url(cfg.client.tag, cfg.client.build_args.VITE_APP_WS_SERVER_URL)


def _verify_baked_url(tag: str, expected: str) -> None:
    """Confirm the expected URL is in the bundle and the public one is gone."""
    probe = (
        f'grep -rl "{expected}" /usr/share/nginx/html/assets | head -1; '
        'grep -rl "oss-collab.excalidraw.com" /usr/share/nginx/html/assets | wc -l'
    )
    result = subprocess.run(
        ["docker", "run", "--rm", tag, "sh", "-c", probe],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        console.print("[red]could not inspect image bundle[/red]")
        raise typer.Exit(1)
    lines = result.stdout.strip().splitlines()
    found = len(lines) > 0 and lines[0]
    oss_collab_count = lines[-1].strip() if lines else "?"
    if not found:
        console.print(f"[red]baked URL {expected} not found in bundle[/red]")
        raise typer.Exit(1)
    if oss_collab_count != "0":
        console.print("[red]oss-collab.excalidraw.com still present in bundle[/red]")
        raise typer.Exit(1)
    console.print(f"[green]ok: {expected} baked in, public collab URL removed[/green]")


if __name__ == "__main__":
    app()
