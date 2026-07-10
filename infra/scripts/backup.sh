#!/usr/bin/env bash
# Backup PostgreSQL (source of truth). Neo4j can be rebuilt via projection rebuild.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"
BACKUP_DIR="${1:-${ROOT_DIR}/backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET_DIR="${BACKUP_DIR}/${TIMESTAMP}"

mkdir -p "${TARGET_DIR}"

POSTGRES_USER="${POSTGRES_USER:-pkb}"
POSTGRES_DB="${POSTGRES_DB:-pkb}"

echo "Backing up PostgreSQL to ${TARGET_DIR}"
docker compose -f "${COMPOSE_FILE}" exec -T postgres \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
  > "${TARGET_DIR}/postgres.sql"

cat > "${TARGET_DIR}/manifest.json" <<EOF
{
  "created_at": "${TIMESTAMP}",
  "postgres_db": "${POSTGRES_DB}",
  "notes": "Restore with infra/scripts/restore.sh, then run projection rebuild."
}
EOF

echo "Backup complete: ${TARGET_DIR}"
