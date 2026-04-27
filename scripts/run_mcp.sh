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

cd mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --host "${MCP_HOST}" --port "${MCP_PORT}"
