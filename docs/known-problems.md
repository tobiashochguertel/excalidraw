# Known problems

## YAML parses some commit SHAs as floats

`config/images.yaml` values like `6e06595` are read by YAML 1.1 as
scientific notation (a float). Any SHA that starts with a digit and
contains `e` must be quoted (`"6e06595"`).

## Hardcoded collaboration URL in the official image

The official `excalidraw/excalidraw` image inlines
`https://oss-collab.excalidraw.com` at build time (from
`.env.production`). Runtime env vars are ignored — a naive deployment
silently routes collaboration through Excalidraw's public servers.
Workaround: build with `VITE_APP_WS_SERVER_URL` (see
`architecture.md`).

## No semver tags

Neither Excalidraw image publishes semantic version tags — only
`latest` and commit-SHA tags. Pinning means either using `latest` (and
documenting when it was pulled) or pinning the digest. This fork pins
base-image digests in the Dockerfile and records the room image digest
in `config/images.yaml`.

## Old room server image

`excalidraw/excalidraw-room:latest` is built on `node:12-alpine` and
has seen little maintenance. It is a tiny, stateless relay, so the risk
is acceptable for a loopback deployment; revisit if upstream publishes a
replacement.

## WebCrypto requires a secure context

Collaboration uses WebCrypto, which only works in secure contexts.
`localhost` qualifies; plain-HTTP access from remote devices fails with
a `generateKey` error. Remote access needs HTTPS.

## Rooms are ephemeral and unauthenticated

The relay stores nothing: rooms vanish when empty, and anyone with a
room link can join. This matches Excalidraw's design (drawings live in
the browser), but it is not a collaboration *storage* solution. If
server-side persistence is ever needed, evaluate
`alswl/excalidraw-collaboration` (adds HTTP scene storage) instead of
building a room server from scratch.
