# Architecture

The fork tracks upstream `excalidraw/excalidraw` master and carries
**one modification**: the `Dockerfile` takes the collaboration server
URL as a build arg instead of hardcoding Excalidraw's public server.

## Why the fork exists

The official `excalidraw/excalidraw` image bakes
`VITE_APP_WS_SERVER_URL` into the JS bundle at build time from
`.env.production`, which points at `https://oss-collab.excalidraw.com`.
Setting the env var on a running container has no effect. To run
collaboration against our own relay, the Dockerfile accepts the URL as
a build arg (process env wins over `.env.production` during the Vite
build).

## Layout (files added by the fork)

| Path | Purpose |
|------|---------|
| `Dockerfile` | Upstream + `ARG VITE_APP_WS_SERVER_URL` / `ENV` (the only modified file) |
| `mise.toml` | Tasks: `build-image`, `verify-collab`, `sync-upstream` |
| `scripts/` | PEP 723 Python scripts the tasks call |
| `config/images.yaml` | Images, build args, ports, digests — drives build/verify |
| `docs/` | This documentation |

Everything except `Dockerfile` is a new file, so upstream syncs never
conflict with it (see `upstream-sync.md`). The upstream `README.md` is
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
