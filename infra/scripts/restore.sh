#!/usr/bin/env bash
# Restore PostgreSQL from a backup directory or SQL file.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup-dir-or-postgres.sql>" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"
INPUT_PATH="$1"

if [[ -d "${INPUT_PATH}" ]]; then
  SQL_FILE="${INPUT_PATH}/postgres.sql"
else
  SQL_FILE="${INPUT_PATH}"
fi

if [[ ! -f "${SQL_FILE}" ]]; then
  echo "SQL file not found: ${SQL_FILE}" >&2
  exit 1
fi

POSTGRES_USER="${POSTGRES_USER:-pkb}"
POSTGRES_DB="${POSTGRES_DB:-pkb}"

echo "Restoring PostgreSQL from ${SQL_FILE}"
docker compose -f "${COMPOSE_FILE}" exec -T postgres \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "${SQL_FILE}"

echo "Restore complete. Rebuild Neo4j projection:"
echo "  make rebuild-projection"
