# E2E testing

Playwright (TypeScript, bun) tests that exercise the deployed
self-hosted Excalidraw stack — the `excalidraw-app` client and the
`excalidraw-room` relay — as a real user would: two browser tabs in one
collaboration room.

## Prerequisites

- The stack must be running (ports from `config/images.yaml`):
  `excalidraw-app` on 44186, `excalidraw-room` on 44749.
- `bun` (used for the test tooling only — the app itself stays on
  yarn).

## Run

```sh
mise run test-e2e                  # = cd e2e && bun run test
cd e2e && bun run test:headed      # watch it run in a real browser
```

Environment overrides:

| Variable | Default | Purpose |
|----------|---------|---------|
| `EXCALIDRAW_URL` | `http://localhost:44186` | App under test |
| `EXCALIDRAW_SYNC_THRESHOLD_MS` | `3000` | Max acceptable sync delay |
| `EXCALIDRAW_BROWSER_CHANNEL` | bundled Chromium | Set to `chrome` for system Chrome |

## Coverage

### Collaboration (`collaboration.spec.ts`)

| Test | Verifies |
|------|----------|
| Tab B joins room started by tab A | Room link flow, both tabs share the `#room=` hash |
| Drawing on A visible on B without interaction | Live sync A→B **plus** regression: no "appears only after clicking" behavior |
| Drawing on B visible on A | Sync works in both directions |
| Background tab catches up on focus | Update is delivered promptly once the tab regains focus |
| Scene present when joining an existing room | New joiner receives the current scene (`fetchScene`) |

### No Excalidraw+ marketing (`marketing.spec.ts`)

| Test | Verifies |
|------|----------|
| No plus banner | `.plus-banner` and "Excalidraw+" text absent |
| Welcome screen has no sign-up | Core entries remain, "Sign up" marketing link gone |
| No plus links anywhere | No `<a>` points at `plus.excalidraw.com` (banner/welcome/menu/help) |

Sync latency is asserted against `EXCALIDRAW_SYNC_THRESHOLD_MS` and
logged per run (loopback measured ≈ 300 ms).

## How scene state is detected

This Excalidraw version paints the scene onto a `<canvas>` — there are
no SVG shapes in the DOM — so the tests use two signals:

1. **Canvas pixel comparison** (`canvasPixels`): proves a shape is
   actually painted.
2. **Welcome screen presence**: the welcome screen only renders while
   the scene is empty, so it disappearing *without interaction* proves
   React re-rendered with the remote scene.

## Findings (2026-09-07)

- Live sync latency ≈ 300 ms both directions; no drops in the relay.
- The manual report "drawings appear only after I click the menu of the
  second window" did **not** reproduce with an active tab — the remote
  scene appears without interaction. The likely causes in a real
  browser are background-tab rendering throttling (hidden tabs pause
  `requestAnimationFrame`; React paints when the tab is focused) or the
  welcome-screen overlay revealing already-arrived content. The
  background-tab test above locks in the focus catch-up behavior.
