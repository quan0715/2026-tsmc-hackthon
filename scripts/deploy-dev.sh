#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="devops/docker-compose.dev.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
  COMPOSE_FILE="devops/docker-compose.yml"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Please install Docker." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "docker compose not found. Install Docker Compose v2+ or docker-compose." >&2
  exit 1
fi

if [[ ! -f backend/.env ]]; then
  echo "backend/.env not found. Copy from backend/.env.example first." >&2
  exit 1
fi

"${COMPOSE[@]}" -f "$COMPOSE_FILE" up -d --build

"${COMPOSE[@]}" -f "$COMPOSE_FILE" ps
