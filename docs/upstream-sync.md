# Upstream sync

The fork tracks `excalidraw/excalidraw` master. Because the only
modified file is the `Dockerfile`, syncing is a plain rebase:

```sh
mise run sync-upstream            # fetch + rebase + verify
mise run sync-upstream -- check   # fetch + verify diff only (no rebase)
```

`check` fails loudly if anything other than the `Dockerfile` differs
from upstream — that would mean upstream changed something we must look
at (or our fork carries an uncommitted change).

After a sync, rebuild the image:

```sh
mise run build-image
cd ~/work/services/kroki && docker compose up -d excalidraw-app
```

If the rebase ever conflicts (upstream touching the Dockerfile), resolve
the conflict manually — keep only the `ARG VITE_APP_WS_SERVER_URL` /
`ENV` addition on top of upstream's version — then re-run
`mise run sync-upstream -- check`.
