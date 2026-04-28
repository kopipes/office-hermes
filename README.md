# Provaliant Brain OS - Hermes Agent Build Pack

Implementasi awal berbasis brief Provaliant Brain OS untuk:
- Postgres + pgvector sebagai structured truth + semantic memory
- FastAPI MCP server sebagai gateway terkontrol
- Hermes skill pack untuk intake, extraction, routing, dan reporting
- Wiki + scripts operasional untuk deployment VPS

## Struktur Utama
- `db/` skema, indeks, RLS, seed
- `mcp-server/` API tools (search/get/report/write)
- `skills/` skill briefs Hermes/OpenClaw
- `scripts/` install, setup db, run mcp, backup, restore, health check
- `wiki/` approved knowledge structure

## Quick Start (Local)
1. Salin env:
```bash
cp .env.example .env
```
2. Jalankan postgres + mcp:
```bash
docker compose up -d
```
3. Setup schema:
```bash
bash scripts/setup_db.sh
```
4. Cek health:
```bash
bash scripts/health_check.sh
```

## Run MCP Tanpa Docker
```bash
bash scripts/run_mcp.sh
```

## Core MCP Endpoints
- `GET /health`
- `POST /brain/query`
- `POST /search_db`
- `POST /search_wiki`
- `POST /search_evidence`
- `POST /get_project`
- `POST /get_vendor`
- `POST /get_budget`
- `POST /get_action_items`
- `POST /generate_report`
- `POST /suggest_wiki_update`
- `POST /write_structured_entry`

Semua endpoint memerlukan header:
```text
Authorization: Bearer <MCP_API_KEY>
```

`POST /brain/query` adalah jalur orkestrator utama untuk Donna / Hermes. Endpoint ini menangani intent classification, entity extraction, cache, tool routing, dan answer formatting sebelum fallback ke raw endpoints.
