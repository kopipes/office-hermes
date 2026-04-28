#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-$HOME/.hermes/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[FAIL] Env file not found: $ENV_FILE"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${PMPV_BASE_URL:-}" ]]; then
  echo "[FAIL] PMPV_BASE_URL is missing in $ENV_FILE"
  exit 1
fi

echo "Base URL: $PMPV_BASE_URL"
echo "Key set: $([[ -n "${PMPV_INTERNAL_API_KEY:-}" ]] && echo yes || echo no)"

check() {
  local name="$1"
  local endpoint="$2"
  local code
  local out="/tmp/pmpv_${name}_$$.out"
  code="$(curl -sS -o "$out" -w '%{http_code}' "$PMPV_BASE_URL$endpoint" \
    -H "x-internal-api-key: ${PMPV_INTERNAL_API_KEY:-}" \
    -H "accept: application/json" || true)"
  echo "$name => HTTP $code"
  head -c 220 "$out" || true
  echo
  rm -f "$out" || true
}

check "moms" "/api/integration/moms"
check "projects" "/api/integration/projects"
check "export" "/api/integration/database/export"
