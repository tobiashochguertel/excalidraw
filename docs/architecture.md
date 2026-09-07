# Architecture

The fork tracks upstream `excalidraw/excalidraw` master and carries
two intentional modifications, both driven by build args:

1. **Collaboration URL** — the Dockerfile takes
   `VITE_APP_WS_SERVER_URL` as a build arg instead of hardcoding
   Excalidraw's public server.
2. **No Excalidraw+ marketing** — the Dockerfile takes
   `VITE_APP_DISABLE_PLUS=true` as a build arg; the fork gates the
   Excalidraw+ UI (banner, sign-up links, command palette entries,
   export-to-plus, help blog link) behind it.

## Why the fork exists

The official `excalidraw/excalidraw` image bakes
`VITE_APP_WS_SERVER_URL` into the JS bundle at build time from
`.env.production`, which points at `https://oss-collab.excalidraw.com`.
Setting the env var on a running container has no effect. To run
collaboration against our own relay, the Dockerfile accepts the URL as
a build arg (process env wins over `.env.production` during the Vite
build). For a self-hosted instance the Excalidraw+ marketing UI is
irrelevant, so a second build arg removes it.

## Layout (files added by the fork)

| Path | Purpose |
|------|---------|
| `Dockerfile` | Upstream + build args (`VITE_APP_WS_SERVER_URL`, `VITE_APP_DISABLE_PLUS`) |
| `excalidraw-app/`, `packages/excalidraw/` | `VITE_APP_DISABLE_PLUS` flag: `IS_PLUS_ENABLED` constant, `PlusEnabled` wrapper component, gated palette/export/help |
| `mise.toml` | Tasks: `build-image`, `verify-collab`, `sync-upstream`, `test-e2e` |
| `scripts/` | PEP 723 Python scripts the tasks call |
| `config/images.yaml` | Images, build args, ports, digests — drives build/verify |
| `docs/` | This documentation |
| `e2e/` | Playwright e2e suite (collaboration + marketing) |

The modified upstream files (Dockerfile + the `VITE_APP_DISABLE_PLUS`
gates) are tracked in `scripts/sync-upstream.py` (`PATCHED_FILES`) so
syncs fail loudly if anything else drifts. The upstream `README.md` is
left untouched.

## Services (deployed from the services repo)

| Service | Image | Purpose |
|---------|-------|---------|
| `excalidraw-app` | `excalidraw:fork-collab` (local build) | Drawing app, collab-enabled |
| `excalidraw-room` | `excalidraw/excalidraw-room:latest` | socket.io relay for real-time collab |

Deployment config (ports, CORS, healthchecks) lives in
`~/work/services/kroki/docker-compose.yml` + `.env`, not in this repo.
`config/images.yaml` mirrors the values the *build* depends on (baked
URL, ports) so builds and verification stay reproducible.
