#!/usr/bin/env bash
set -o pipefail

BASE_URL="${WIZARD_URL:-http://localhost:8765}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"

hdr_auth=()
if [[ -n "$ADMIN_TOKEN" ]]; then
  hdr_auth=("-H" "Authorization: Bearer ${ADMIN_TOKEN}")
fi

request() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"
  local url="${BASE_URL}${path}"

  if [[ -n "$data" ]]; then
    status=$(curl -s -o /tmp/smoke_response.json -w "%{http_code}" -X "$method" \
      "${hdr_auth[@]}" -H "Content-Type: application/json" \
      -d "$data" "$url" || true)
  else
    status=$(curl -s -o /tmp/smoke_response.json -w "%{http_code}" -X "$method" \
      "${hdr_auth[@]}" "$url" || true)
  fi
  echo "$method $path -> $status"
}

echo "Wizard smoke: ${BASE_URL}"

# Binder
request GET "/api/binder/workspaces"
request GET "/api/binder?workspace=sandbox"
request GET "/api/binder/summary"

BINDER_ID="smoke-$(date +%s)"
request POST "/api/binder" "{\"binder_id\":\"${BINDER_ID}\",\"title\":\"Smoke Binder\",\"workspace\":\"sandbox\"}"
request POST "/api/binder/${BINDER_ID}/chapters" "{\"title\":\"Intro\",\"content\":\"# Intro\\n\\nSmoke test\",\"order\":1}"
request POST "/api/binder/${BINDER_ID}/compile" "{\"binder_id\":\"${BINDER_ID}\",\"formats\":[\"markdown\",\"json\"]}"

# Sonic
request GET "/api/sonic/health"
request GET "/api/sonic/schema"
request GET "/api/sonic/stats"
request GET "/api/sonic/devices?limit=1"

# Screwdriver
request GET "/api/sonic/screwdriver/schema"
request GET "/api/sonic/screwdriver/flash-packs"

exit 0
