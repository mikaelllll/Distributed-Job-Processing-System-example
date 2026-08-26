#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  prefix="https://${CODESPACE_NAME}"
  domain="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  frontend_url="${prefix}-3000.${domain}"

  echo
  echo "Dispatch frontend: ${frontend_url}"
  echo "FastAPI documentation: ${prefix}-8000.${domain}/docs"
  echo "RabbitMQ management: ${prefix}-15672.${domain}"
  echo "Grafana: ${prefix}-3001.${domain}"
  echo "Prometheus: ${prefix}-9090.${domain}"
  echo

  if [[ "${1:-}" == "--open-frontend" && -n "${BROWSER:-}" ]]; then
    "${BROWSER}" "${frontend_url}" >/dev/null 2>&1 || true
  fi
else
  echo
  echo "Dispatch frontend: http://localhost:3000"
  echo "FastAPI documentation: http://localhost:8000/docs"
  echo "RabbitMQ management: http://localhost:15672"
  echo "Grafana: http://localhost:3001"
  echo "Prometheus: http://localhost:9090"
  echo
fi
