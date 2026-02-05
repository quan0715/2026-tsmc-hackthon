#!/usr/bin/env bash
set -euo pipefail

REQUIRED_VARS=(REGISTRY_HOST GCP_PROJECT_ID GAR_REPOSITORY)
MISSING=()
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    MISSING+=("$var")
  fi
done

if (( ${#MISSING[@]} > 0 )); then
  echo "Missing required env vars: ${MISSING[*]}" >&2
  echo "Example:" >&2
  echo "  export REGISTRY_HOST=us-central1-docker.pkg.dev" >&2
  echo "  export GCP_PROJECT_ID=your-project" >&2
  echo "  export GAR_REPOSITORY=refactor" >&2
  exit 1
fi

IMAGE_TAG=${IMAGE_TAG:-latest}
BASE_IMAGE_TAG=${BASE_IMAGE_TAG:-$IMAGE_TAG}
WORKSPACE_HOST_DIR=${WORKSPACE_HOST_DIR:-/var/lib/refactor-workspaces}
COMPOSE_FILE="devops/docker-compose.prod.yml"

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

if ! mkdir -p "$WORKSPACE_HOST_DIR" 2>/dev/null; then
  echo "Failed to create $WORKSPACE_HOST_DIR (need sudo?)." >&2
  echo "Try: sudo mkdir -p $WORKSPACE_HOST_DIR && sudo chown $USER:$USER $WORKSPACE_HOST_DIR" >&2
  exit 1
fi

BASE_IMAGE_REMOTE="${REGISTRY_HOST}/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/refactor-base:${BASE_IMAGE_TAG}"

docker pull "$BASE_IMAGE_REMOTE"
docker tag "$BASE_IMAGE_REMOTE" refactor-base:latest

"${COMPOSE[@]}" -f "$COMPOSE_FILE" pull
"${COMPOSE[@]}" -f "$COMPOSE_FILE" up -d

"${COMPOSE[@]}" -f "$COMPOSE_FILE" ps
