#!/bin/sh
set -eu

NETWORK_NAME="${CADDY_NETWORK:-caddy}"

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  docker network create "$NETWORK_NAME"
fi

docker compose up -d
