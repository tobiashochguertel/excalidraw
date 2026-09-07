# Rebuild & deploy

The client image is built locally from this checkout and referenced by
the services repo compose file (`~/work/services/kroki`).

## Build

```sh
# from the fork root
mise run build-image            # = uv run --script scripts/build-image.py
```

The build args come from `config/images.yaml`; the base images are
digest-pinned in the Dockerfile, so identical inputs produce identical
images. `mise run build-image -- --check` also verifies the baked URL
after building.

## Deploy

The compose file expects the local image tag `excalidraw:fork-collab`:

```sh
cd ~/work/services/kroki
docker compose up -d excalidraw-app excalidraw-room
```

## Verify

```sh
mise run verify-collab
```

## Changing the room port

The room URL is baked into the client image, so changing
`EXCALIDRAW_ROOM_PORT` requires:

1. update `config/images.yaml` (`client.build_args` +
   `room.port`)
2. `mise run build-image`
3. update `.env` in `~/work/services/kroki`
4. `docker compose up -d excalidraw-app excalidraw-room`
