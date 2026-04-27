# Installation Guide

1. Copy environment file:
```bash
cp .env.example .env
```
2. Start services:
```bash
docker compose up -d
```
3. Setup database:
```bash
bash scripts/setup_db.sh
```
4. Start MCP server (if not dockerized):
```bash
bash scripts/run_mcp.sh
```
