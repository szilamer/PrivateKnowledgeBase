#!/usr/bin/env bash
# End-to-end smoke test against a running Docker Compose stack.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
FIXTURES_PATH="${FIXTURES_PATH:-/fixtures}"
POLL_INTERVAL="${POLL_INTERVAL:-3}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-180}"

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

wait_for() {
  local description="$1"
  local cmd="$2"
  local elapsed=0
  while ! eval "$cmd" >/dev/null 2>&1; do
    if [[ "${elapsed}" -ge "${MAX_WAIT_SECONDS}" ]]; then
      fail "${description} (timeout after ${MAX_WAIT_SECONDS}s)"
    fi
    sleep "${POLL_INTERVAL}"
    elapsed=$((elapsed + POLL_INTERVAL))
  done
  pass "${description}"
}

echo "=== PKB E2E Smoke Test ==="
echo "API: ${API_URL}"
echo "Fixtures path (container): ${FIXTURES_PATH}"

wait_for "API health" "curl -sf '${API_URL}/api/v1/health' | grep -q healthy"

OPS_STATUS="$(curl -sf "${API_URL}/api/v1/operations/status")"
echo "${OPS_STATUS}" | grep -q '"pending_outbox_events"' || fail "operations status schema"
pass "operations status endpoint"

SOURCE_RESPONSE="$(curl -sf -X POST "${API_URL}/api/v1/sources/local" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"E2E Smoke Source\",\"path\":\"${FIXTURES_PATH}\",\"file_extensions\":[\".md\"]}" )"
SOURCE_ID="$(echo "${SOURCE_RESPONSE}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
[[ -n "${SOURCE_ID}" ]] || fail "register local source"
pass "register local source (${SOURCE_ID})"

SYNC_RESPONSE="$(curl -sf -X POST "${API_URL}/api/v1/sync-runs" \
  -H 'Content-Type: application/json' \
  -d "{\"source_id\":\"${SOURCE_ID}\",\"mode\":\"full\"}")"
SYNC_ID="$(echo "${SYNC_RESPONSE}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
[[ -n "${SYNC_ID}" ]] || fail "start sync run"
pass "start sync run (${SYNC_ID})"

wait_for "sync run completion" "curl -sf '${API_URL}/api/v1/sync-runs/${SYNC_ID}' | python3 -c 'import json,sys; s=json.load(sys.stdin)[\"status\"]; raise SystemExit(0 if s in (\"completed\",\"partial\") else 1)'"

SYNC_FINAL="$(curl -sf "${API_URL}/api/v1/sync-runs/${SYNC_ID}")"
echo "${SYNC_FINAL}" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["objects_processed"]>=1, d'
pass "sync processed at least one object"

echo "Waiting for worker pipeline (chunking, extraction, proposals)..."
wait_for "pending proposals available" "curl -sf '${API_URL}/api/v1/proposals?status=pending&limit=1' | python3 -c 'import json,sys; raise SystemExit(0 if json.load(sys.stdin)[\"items\"] else 1)'"

PROPOSALS="$(curl -sf "${API_URL}/api/v1/proposals?status=pending&limit=20")"
APPROVED=0
while IFS= read -r proposal_id; do
  [[ -z "${proposal_id}" ]] && continue
  curl -sf -X POST "${API_URL}/api/v1/proposals/${proposal_id}/approve" \
    -H 'Content-Type: application/json' \
    -d '{}' >/dev/null || true
  APPROVED=$((APPROVED + 1))
done < <(echo "${PROPOSALS}" | python3 -c 'import json,sys; [print(p["id"]) for p in json.load(sys.stdin)["items"]]')

[[ "${APPROVED}" -ge 1 ]] || fail "approve at least one proposal"
pass "approved ${APPROVED} proposal(s)"

echo "Waiting for graph projection..."
wait_for "outbox drain" "curl -sf '${API_URL}/api/v1/operations/status' | python3 -c 'import json,sys; raise SystemExit(0 if json.load(sys.stdin)[\"pending_outbox_events\"]==0 else 1)'" || true

SEARCH_RESPONSE="$(curl -sf -X POST "${API_URL}/api/v1/search" \
  -H 'Content-Type: application/json' \
  -d '{"query":"PostgreSQL outbox","mode":"hybrid","limit":5}')"
echo "${SEARCH_RESPONSE}" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert len(d.get("hits",[]))>=1, d'
pass "search returns hits"

QA_RESPONSE="$(curl -sf -X POST "${API_URL}/api/v1/questions" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What technologies does the MVP use?","mode":"hybrid","limit":10}')"
echo "${QA_RESPONSE}" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("answer"), d'
pass "question answering returns an answer"

DASHBOARD="$(curl -sf "${API_URL}/api/v1/projects/overview")"
echo "${DASHBOARD}" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert "summary" in d'
pass "project dashboard"

REBUILD="$(curl -sf -X POST "${API_URL}/api/v1/operations/projection/rebuild")"
echo "${REBUILD}" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("cleared_nodes") is True'
pass "projection rebuild"

echo ""
echo "=== E2E SMOKE TEST PASSED ==="
