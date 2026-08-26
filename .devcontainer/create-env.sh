#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  exit 0
fi

umask 077
postgres_password="$(openssl rand -hex 24)"
rabbitmq_password="$(openssl rand -hex 24)"
grafana_password="$(openssl rand -hex 24)"

printf '%s\n' \
  'POSTGRES_DB=job_platform' \
  'POSTGRES_USER=job_platform' \
  "POSTGRES_PASSWORD=${postgres_password}" \
  "DATABASE_URL=postgresql+asyncpg://job_platform:${postgres_password}@postgres:5432/job_platform" \
  'RABBITMQ_USER=job_platform' \
  "RABBITMQ_PASSWORD=${rabbitmq_password}" \
  "RABBITMQ_URL=amqp://job_platform:${rabbitmq_password}@rabbitmq:5672/" \
  'REDIS_URL=redis://redis:6379/0' \
  'GRAFANA_ADMIN_USER=admin' \
  "GRAFANA_ADMIN_PASSWORD=${grafana_password}" \
  'CORS_ORIGINS=http://localhost:3000,http://localhost:5173' \
  'PUBLIC_MAX_JOBS=1000000' \
  'METRICS_FLUSH_INTERVAL_SECONDS=2' \
  > .env

echo 'Created .env with random local credentials.'
