#!/usr/bin/env bash
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_BIN="${HERMES_BIN:-$HOME/.local/bin/hermes}"
OFFICE_HERMES_DIR="${OFFICE_HERMES_DIR:-$HOME/office-hermes}"
RUN_LLM_TEST="${RUN_LLM_TEST:-0}"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf '[PASS] %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf '[WARN] %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf '[FAIL] %s\n' "$1"
}

print_header() {
  printf '\n=== %s ===\n' "$1"
}

http_code() {
  local method="$1"
  local url="$2"
  local auth="$3"
  local body="${4:-}"

  if [[ "$method" == "GET" ]]; then
    curl -sS -o /tmp/audit_api_body.out -w '%{http_code}' "$url" \
      -H "Authorization: Bearer $auth"
  else
    curl -sS -o /tmp/audit_api_body.out -w '%{http_code}' "$url" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $auth" \
      -d "$body"
  fi
}

print_header "Host Context"
printf 'User: %s\n' "$(whoami)"
printf 'Host: %s\n' "$(hostname)"
printf 'Date: %s\n' "$(date -Iseconds)"

print_header "Hermes Runtime"
if [[ -x "$HERMES_BIN" ]]; then
  HERMES_VERSION="$("$HERMES_BIN" --version 2>/dev/null | head -n 1 || true)"
  if [[ "$HERMES_VERSION" == Hermes\ Agent* ]]; then
    pass "Hermes binary found at $HERMES_BIN ($HERMES_VERSION)"
  else
    warn "Hermes binary exists but version output unexpected"
  fi
else
  fail "Hermes binary not found at $HERMES_BIN"
fi

if [[ -d "$HERMES_HOME" && -f "$HERMES_HOME/config.yaml" ]]; then
  pass "Hermes home/config detected at $HERMES_HOME"
else
  fail "Hermes home/config missing ($HERMES_HOME/config.yaml)"
fi

print_header "Model and Fallback"
FALLBACK_OUT="$("$HERMES_BIN" fallback list 2>/dev/null || true)"
if [[ "$FALLBACK_OUT" == *"inclusionai/ling-2.6-1t:free"* ]]; then
  pass "Primary model detected: inclusionai/ling-2.6-1t:free"
else
  fail "Primary model mismatch (expected inclusionai/ling-2.6-1t:free)"
fi

for model in \
  "tencent/hy3-preview:free" \
  "inclusionai/ling-2.6-flash:free" \
  "minimax/minimax-m2.5:free"
do
  if [[ "$FALLBACK_OUT" == *"$model"* ]]; then
    pass "Fallback model detected: $model"
  else
    fail "Fallback model missing: $model"
  fi
done

print_header "Local Skill"
SKILL_FILE="$HERMES_HOME/skills/provaliant-brain-os-query/SKILL.md"
if [[ -f "$SKILL_FILE" ]]; then
  pass "Skill file exists: $SKILL_FILE"
else
  fail "Skill file missing: $SKILL_FILE"
fi

if [[ -f "$SKILL_FILE" ]]; then
  if grep -q "Authorization: Bearer" "$SKILL_FILE"; then
    pass "Skill auth header format is Bearer"
  else
    fail "Skill auth header format invalid (Bearer not found)"
  fi

  for endpoint in "/get_project" "/search_db" "/generate_report"; do
    if grep -q "$endpoint" "$SKILL_FILE"; then
      pass "Skill contains endpoint template $endpoint"
    else
      warn "Skill missing endpoint template $endpoint"
    fi
  done
fi

print_header "Systemd Services"
if systemctl --user is-active hermes-gateway.service >/dev/null 2>&1; then
  pass "hermes-gateway.service is active"
else
  fail "hermes-gateway.service is not active"
fi

if systemctl --user is-active office-hermes-mcp.service >/dev/null 2>&1; then
  pass "office-hermes-mcp.service is active"
else
  fail "office-hermes-mcp.service is not active"
fi

print_header "MCP API Checks"
ENV_FILE="$OFFICE_HERMES_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  pass "Office Hermes env found: $ENV_FILE"
else
  fail "Office Hermes env missing: $ENV_FILE"
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ -n "${MCP_HOST:-}" && -n "${MCP_PORT:-}" && -n "${MCP_API_KEY:-}" ]]; then
  pass "MCP host/port/api_key variables are present"
else
  fail "MCP_HOST/MCP_PORT/MCP_API_KEY missing in $ENV_FILE"
fi

API_BASE="http://${MCP_HOST:-127.0.0.1}:${MCP_PORT:-8000}"

if [[ -n "${MCP_API_KEY:-}" ]]; then
  CODE="$(http_code GET "$API_BASE/health" "$MCP_API_KEY")"
  if [[ "$CODE" == "200" ]]; then
    pass "GET /health returned HTTP 200"
  else
    fail "GET /health returned HTTP $CODE: $(cat /tmp/audit_api_body.out)"
  fi

  CODE="$(http_code POST "$API_BASE/get_project" "$MCP_API_KEY" '{"project_code_or_name":"CPP","user_id":"donna","role":"admin"}')"
  if [[ "$CODE" == "200" ]]; then
    pass "POST /get_project returned HTTP 200"
  else
    fail "POST /get_project returned HTTP $CODE: $(cat /tmp/audit_api_body.out)"
  fi

  CODE="$(http_code POST "$API_BASE/search_db" "$MCP_API_KEY" '{"query":"CPP","limit":5}')"
  if [[ "$CODE" == "200" ]]; then
    pass "POST /search_db returned HTTP 200"
  else
    fail "POST /search_db returned HTTP $CODE: $(cat /tmp/audit_api_body.out)"
  fi

  CODE="$(http_code POST "$API_BASE/generate_report" "$MCP_API_KEY" '{"query":"weekly_executive","limit":20}')"
  if [[ "$CODE" == "200" ]]; then
    pass "POST /generate_report returned HTTP 200"
  else
    fail "POST /generate_report returned HTTP $CODE: $(cat /tmp/audit_api_body.out)"
  fi
fi

print_header "Database Checks"
if command -v psql >/dev/null 2>&1; then
  pass "psql is available"
else
  fail "psql command not found"
fi

if [[ -n "${DATABASE_URL:-}" ]] && command -v psql >/dev/null 2>&1; then
  TABLE_COUNT="$(psql "$DATABASE_URL" -tAc "select count(*) from information_schema.tables where table_schema='public';" 2>/dev/null || echo "")"
  if [[ -n "$TABLE_COUNT" && "$TABLE_COUNT" -ge 20 ]]; then
    pass "Public table count is $TABLE_COUNT (>=20)"
  else
    fail "Public table count check failed (value: ${TABLE_COUNT:-empty})"
  fi

  VECTOR_EXT="$(psql "$DATABASE_URL" -tAc "select extname from pg_extension where extname='vector';" 2>/dev/null || true)"
  if [[ "$VECTOR_EXT" == "vector" ]]; then
    pass "pgvector extension is enabled"
  else
    warn "pgvector extension not detected"
  fi

  if psql "$DATABASE_URL" -tAc "select count(*) from query_logs;" >/dev/null 2>&1; then
    pass "query_logs table is accessible"
  else
    fail "query_logs table inaccessible"
  fi

  if psql "$DATABASE_URL" -tAc "select count(*) from audit_logs;" >/dev/null 2>&1; then
    pass "audit_logs table is accessible"
  else
    fail "audit_logs table inaccessible"
  fi
else
  fail "DATABASE_URL is missing; cannot run DB checks"
fi

print_header "Telegram Pairing Check"
APPROVED_FILE="$HERMES_HOME/pairing/telegram-approved.json"
if [[ -f "$APPROVED_FILE" ]]; then
  pass "telegram-approved.json exists"
  if command -v jq >/dev/null 2>&1; then
    APPROVED_LEN="$(jq 'length' "$APPROVED_FILE" 2>/dev/null || echo 0)"
    if [[ "${APPROVED_LEN:-0}" -ge 1 ]]; then
      pass "Telegram approved entries detected ($APPROVED_LEN)"
    else
      warn "Telegram approved file exists but has no entries"
    fi
  else
    warn "jq not installed; cannot validate approved pairing count"
  fi
else
  warn "telegram-approved.json not found"
fi

print_header "Optional One-Shot LLM Smoke Test"
if [[ "$RUN_LLM_TEST" == "1" ]]; then
  ONESHOT_OUT="$("$HERMES_BIN" -z "Reply with exactly: READY" 2>/dev/null || true)"
  if [[ "$ONESHOT_OUT" == "READY" ]]; then
    pass "Hermes one-shot LLM test passed"
  else
    fail "Hermes one-shot LLM test failed (output: ${ONESHOT_OUT:-empty})"
  fi
else
  warn "Skipped one-shot LLM test (set RUN_LLM_TEST=1 to enable)"
fi

rm -f /tmp/audit_api_body.out

print_header "Summary"
printf 'PASS: %d\n' "$PASS_COUNT"
printf 'WARN: %d\n' "$WARN_COUNT"
printf 'FAIL: %d\n' "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

exit 0
