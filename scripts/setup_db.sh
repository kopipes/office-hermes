#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo ".env not found. Create it from .env.example first."
  exit 1
fi

set -a
source .env
set +a

echo "=== Setting up Provaliant Brain OS database ==="

sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE ${POSTGRES_DB};"

sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};"

sudo -u postgres psql -d "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/indexes.sql
psql "$DATABASE_URL" -f db/rls.sql
psql "$DATABASE_URL" -f db/seeds/roles.sql
psql "$DATABASE_URL" -f db/seeds/business_units.sql
psql "$DATABASE_URL" -f db/seeds/users.sql

echo "Database setup complete."
