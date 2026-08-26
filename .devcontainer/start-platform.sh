#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

if curl --fail --silent http://127.0.0.1:8000/health/ready >/dev/null 2>&1 \
  && curl --fail --silent http://127.0.0.1:3000/healthz >/dev/null 2>&1; then
  echo "Platform is already running."
  bash .devcontainer/print-urls.sh
  exit 0
fi

worker_replicas="${WORKER_REPLICAS:-4}"

echo "Starting the complete platform with ${worker_replicas} workers..."
docker compose up -d --build --scale "worker=${worker_replicas}"

echo "Waiting for the frontend and API..."
for attempt in $(seq 1 90); do
  if curl --fail --silent http://127.0.0.1:8000/health/ready >/dev/null \
    && curl --fail --silent http://127.0.0.1:3000/healthz >/dev/null; then
    echo "Platform is ready."
    bash .devcontainer/print-urls.sh
    exit 0
  fi
  sleep 2
done

echo "The platform did not become healthy within three minutes."
docker compose ps
docker compose logs --tail=100 api frontend
exit 1
