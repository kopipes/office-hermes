#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

set -a
source .env
set +a

mkdir -p "$BACKUP_PATH"
TS=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_PATH/provaliant_brain_${TS}.sql.gz"

pg_dump "$DATABASE_URL" | gzip > "$OUT"
find "$BACKUP_PATH" -type f -name "*.sql.gz" -mtime +"${BACKUP_RETENTION_DAYS}" -delete

echo "Backup created: $OUT"
