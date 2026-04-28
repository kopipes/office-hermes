# PMPV API Setup (Hermes)

Source guide checked from `Archive.zip`:
- `SKILL.md`
- `INSTALL.md`
- `pmpv-sync.env.example`
- `pmpv-sync-variables.md`

## Required Variables

Add these to `~/.hermes/.env` on VPS:

```env
PMPV_BASE_URL=https://pm.provaliantgroup.com
PMPV_INTERNAL_API_KEY=REPLACE_WITH_STRONG_SECRET
PMPV_SYNC_INTERVAL=10m
PMPV_SYNC_BATCH_SIZE=100
PMPV_CACHE_PATH=/home/ubuntu/.hermes/data/pmpv-cache.sqlite
```

Recommended extras (from bundle):

```env
PMPV_SYNC_ON_STARTUP=true
PMPV_SYNC_ON_DEMAND=true
PMPV_SYNC_RETRY_LIMIT=3
PMPV_SYNC_BACKOFF_MS=2000
PMPV_CACHE_ENABLE_FTS=true
PMPV_CACHE_ENABLE_VECTOR=false
PMPV_CACHE_TTL=24h
PMPV_CACHE_MAX_RECORDS=100000
PMPV_CACHE_REBUILD_ON_STARTUP=false
PMPV_RETRIEVAL_MODE=cache-first
PMPV_RETRIEVAL_TOP_K=5
PMPV_RETRIEVAL_MAX_CHUNKS=5
PMPV_RETRIEVAL_USE_FALLBACK_API=true
PMPV_RETRIEVAL_MIN_SCORE=0.65
PMPV_INDEX_MODE=fts
PMPV_INDEX_CHUNK_SIZE=500
PMPV_INDEX_CHUNK_OVERLAP=50
PMPV_INDEX_REFRESH_ON_SYNC=true
PMPV_LLM_ONLY_FINAL_ANSWER=true
PMPV_LLM_TEMPERATURE=0.2
PMPV_LLM_MAX_INPUT_TOKENS=4000
PMPV_LLM_MAX_OUTPUT_TOKENS=800
PMPV_ANSWER_STYLE=ringkas-faktual
PMPV_REQUIRE_INTERNAL_KEY=true
PMPV_REQUIRE_ALLOWLIST_IP=true
PMPV_ALLOW_STALE_CACHE_ON_FAIL=true
PMPV_NEVER_USE_DIRECT_DB=true
PMPV_LOG_LEVEL=info
```

## Runtime Skill Path

Install skill to:

`~/.hermes/skills/pmpv-sync/SKILL.md`

## Connectivity Check

Use:

```bash
bash scripts/pmpv_api_check.sh ~/.hermes/.env
```

Expected behavior:
- Missing/invalid key -> `401`
- Key valid but IP not allowlisted -> `403`
- Key valid and IP allowlisted -> `200`
