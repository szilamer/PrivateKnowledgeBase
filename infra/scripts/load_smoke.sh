#!/usr/bin/env bash
# Lightweight load smoke against a running API stack.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
REQUESTS="${REQUESTS:-50}"

echo "Load smoke: ${REQUESTS} health checks against ${API_URL}"
failures=0
for _ in $(seq 1 "${REQUESTS}"); do
  if ! curl -sf "${API_URL}/api/v1/health" > /dev/null; then
    failures=$((failures + 1))
  fi
done

if [[ "${failures}" -gt 0 ]]; then
  echo "FAILED: ${failures}/${REQUESTS} requests failed" >&2
  exit 1
fi

echo "OK: ${REQUESTS}/${REQUESTS} health checks succeeded"
