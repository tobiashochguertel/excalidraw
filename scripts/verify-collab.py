#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0",
#   "pydantic>=2.7",
#   "ruamel.yaml>=0.18",
#   "httpx>=0.27",
# ]
# [tool.uv]
# exclude-newer = "2026-09-01T00:00:00Z"
# ///
"""
verify-collab.py

Verify the self-hosted Excalidraw collaboration setup:

1. `image` — the built client image (excalidraw:fork-collab) contains
   the configured VITE_APP_WS_SERVER_URL and no longer references
   Excalidraw's public collab server.
2. `room`  — the excalidraw-room relay answers an engine.io polling
   handshake on the configured port.

Usage:
    uv run --script scripts/verify-collab.py        # run both checks
    uv run --script scripts/verify-collab.py image  # image check only
    uv run --script scripts/verify-collab.py room   # room check only

Environment variables:
    EXCALIDRAW_IMAGES_CONFIG  Config file path override (default: config/images.yaml)
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import httpx
import typer
from pydantic import BaseModel
from rich.console import Console
from ruamel.yaml import YAML

_ENV_CONFIG = "EXCALIDRAW_IMAGES_CONFIG"
_DEFAULT_CONFIG = Path("config/images.yaml")

console = Console(stderr=True)

app = typer.Typer(
    name="verify-collab",
    help="Verify the Excalidraw collaboration setup (baked URL + room relay).",
    add_completion=True,
    # Note: no no_args_is_help here — the callback is the default command
    # (runs both checks) and no_args_is_help would shadow it.
)


class ClientConfig(BaseModel):
    tag: str
    build_args: dict[str, str]


class RoomConfig(BaseModel):
    port: int


class ImagesConfig(BaseModel):
    client: ClientConfig
    room: RoomConfig


def _load_config(cli: Path | None) -> ImagesConfig:
    raw: str | Path | None = cli
    if raw is None:
        raw = os.environ.get(_ENV_CONFIG)
    if raw is None:
        path = Path.cwd() / _DEFAULT_CONFIG
    else:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
    yaml = YAML(typ="safe")
    return ImagesConfig.model_validate(yaml.load(path.read_text(encoding="utf-8")))


def _check_image(cfg: ImagesConfig) -> bool:
    tag = cfg.client.tag
    expected = cfg.client.build_args["VITE_APP_WS_SERVER_URL"]
    probe = (
        f'grep -rl "{expected}" /usr/share/nginx/html/assets | head -1; '
        'grep -rl "oss-collab.excalidraw.com" /usr/share/nginx/html/assets | wc -l'
    )
    result = subprocess.run(
        ["docker", "run", "--rm", tag, "sh", "-c", probe],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]image {tag}: could not inspect bundle ({result.stderr.strip()})[/red]")
        return False
    lines = result.stdout.strip().splitlines()
    found = bool(lines and lines[0])
    public_left = bool(lines and lines[-1].strip() != "0")
    if not found:
        console.print(f"[red]image {tag}: baked URL {expected} not found[/red]")
    elif public_left:
        console.print(f"[red]image {tag}: oss-collab.excalidraw.com still present[/red]")
    else:
        console.print(f"[green]image {tag}: {expected} baked in, public collab URL removed[/green]")
    return found and not public_left


def _check_room(cfg: ImagesConfig) -> bool:
    port = cfg.room.port
    url = f"http://localhost:{port}/socket.io/?EIO=4&transport=polling"
    try:
        resp = httpx.get(url, timeout=5)
    except httpx.HTTPError as exc:
        console.print(f"[red]room relay {url}: {exc}[/red]")
        return False
    ok = resp.status_code == 200 and '"sid"' in resp.text
    if ok:
        console.print(f"[green]room relay {url}: handshake ok (HTTP {resp.status_code})[/green]")
    else:
        console.print(f"[red]room relay {url}: unexpected response HTTP {resp.status_code}[/red]")
    return ok


@app.command()
def image(
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Images config file path.",
        envvar=_ENV_CONFIG, show_default=True,
    ),
) -> None:
    """Check the built client image for the baked collab URL."""
    if not _check_image(_load_config(config)):
        raise typer.Exit(1)


@app.command()
def room(
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Images config file path.",
        envvar=_ENV_CONFIG, show_default=True,
    ),
) -> None:
    """Check the excalidraw-room relay handshake."""
    if not _check_room(_load_config(config)):
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Images config file path.",
        envvar=_ENV_CONFIG, show_default=True,
    ),
) -> None:
    """Run both checks when no subcommand is given."""
    if ctx.invoked_subcommand is not None:
        return
    cfg = _load_config(config)
    ok_image = _check_image(cfg)
    ok_room = _check_room(cfg)
    if not (ok_image and ok_room):
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
