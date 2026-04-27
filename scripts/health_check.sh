#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

set -a
source .env
set +a

echo "Checking Postgres..."
pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT"

echo "Checking MCP server..."
curl -s -H "Authorization: Bearer $MCP_API_KEY" "http://localhost:${MCP_PORT}/health" | jq .

echo "Checking core tables..."
psql "$DATABASE_URL" -c "select count(*) as projects from projects;"
psql "$DATABASE_URL" -c "select count(*) as documents from documents;"
psql "$DATABASE_URL" -c "select count(*) as wiki_pages from wiki_pages;"

echo "Health check complete."
