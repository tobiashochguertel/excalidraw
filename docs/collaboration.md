# Collaboration

The app at `http://localhost:44186` connects to the local
`excalidraw-room` relay (`ws://localhost:44749`, baked into the image).
Open the app in two tabs/browsers, hit the collaboration icon and share
the room link.

## How it works

- The client encrypts the scene with WebCrypto and streams updates to
  the relay; the relay is a stateless in-memory socket.io server that
  fans messages out to room members. No drawing data is stored
  server-side.
- `localhost` is a secure context, so WebCrypto works without HTTPS.
  Remote devices would need HTTPS (e.g. a reverse proxy) for
  collaboration to function.
- Rooms vanish when empty; drawings persist in the browser
  (localStorage) and via `.excalidraw` export. Anyone with a room link
  can join — there is no authentication, which is fine for a
  loopback-only deployment.

## Rendering to Kroki

Excalidraw scenes render through the local Kroki gateway
(`http://localhost:44053`):

1. Export the scene in the app (menu → Export image → *Export
   .excalidraw file*). The file is JSON (`elements` + `appState`).
2. Paste the JSON into Kroki Editor (type `excalidraw`,
   `http://localhost:44812`) or POST it:

   ```sh
   curl -s http://localhost:44053/excalidraw/svg --data-binary @scene.excalidraw
   ```

Kroki itself only renders scenes — it ships no drawing UI (see
`architecture.md`).

## Verification

```sh
mise run verify-collab
```

Checks the built image contains the baked URL (and no longer the public
one) and that the relay answers an engine.io handshake.
