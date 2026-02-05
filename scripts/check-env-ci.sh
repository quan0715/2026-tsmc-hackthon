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
  exit 1
fi

REQUIRED_FILES=(
  "devops/base-image/Dockerfile"
  "backend/Dockerfile.prod"
  "frontend/Dockerfile.prod"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required file: $f" >&2
    exit 1
  fi
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found." >&2
  exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
  echo "Docker Buildx not available." >&2
  exit 1
fi

echo "CI environment check passed."
