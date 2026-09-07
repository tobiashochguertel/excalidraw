FROM --platform=${BUILDPLATFORM} node:24@sha256:8530f76a96d88820d288761f022e318970dda93d01536919fbc16076b7983e63 AS build

WORKDIR /opt/node_app

COPY . .

# do not ignore optional dependencies:
# Error: Cannot find module @rollup/rollup-linux-x64-gnu
RUN --mount=type=cache,target=/root/.cache/yarn \
    npm_config_target_arch=${TARGETARCH} yarn --frozen-lockfile --network-timeout 600000

ARG NODE_ENV=production

# Collab server URL, baked in at build time. Vite inlines it and process
# env wins over .env.production (which defaults to Excalidraw's public
# server https://oss-collab.excalidraw.com).
# Build: docker build --build-arg VITE_APP_WS_SERVER_URL=ws://localhost:44749 -t excalidraw:fork-collab .
ARG VITE_APP_WS_SERVER_URL
ENV VITE_APP_WS_SERVER_URL=$VITE_APP_WS_SERVER_URL

# Fork: set to "true" to remove the Excalidraw+ marketing UI from the
# self-hosted build.
ARG VITE_APP_DISABLE_PLUS
ENV VITE_APP_DISABLE_PLUS=$VITE_APP_DISABLE_PLUS

RUN npm_config_target_arch=${TARGETARCH} yarn build:app:docker

FROM nginx:stable-alpine-slim@sha256:2c605dbeab79a6b2a63340474fe58119d0ef95bdc4b1f41df0aa689659b3d13b

COPY --from=build /opt/node_app/excalidraw-app/build /usr/share/nginx/html

HEALTHCHECK CMD wget -q -O /dev/null http://localhost || exit 1
