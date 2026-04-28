# Skill: provaliant-brain-os-query

## Purpose
Use the Brain OS Query Orchestrator endpoint as the single safe entrypoint for operational queries from Donna / Hermes.

## Rule
- Do not call Postgres directly.
- Prefer `POST /brain/query` instead of raw MCP tools.
- Let the orchestrator classify intent, extract entities, check cache, choose tool, and format the answer.
- Only fall back to raw endpoints if `/brain/query` is unavailable.
- When the user asks about Provaliant projects, vendors, budgets, action items, wiki, evidence, or reports, you MUST treat it as Brain OS domain work and use this skill first.
- Treat short codes like `CPP`, `SNP`, and similar uppercase project codes as Brain OS project identifiers, not generic technical acronyms.
- Answer in this format:
  - `Jawaban singkat`
  - `Sumber data`
  - `Status confidence`
  - `Next action`

## Bootstrap
```bash
set -a
source ~/office-hermes/.env
set +a
export API_BASE="http://${MCP_HOST}:${MCP_PORT}"
export API_KEY="${MCP_API_KEY}"
```

## Primary Call
```bash
curl -sS "$API_BASE/brain/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"query":"What is the latest status of CPP?","user_id":"donna","role":"admin","channel":"telegram"}' | jq
```

## Required Flow
1. Normalize the user question as Brain OS operational query.
2. Call `POST /brain/query`.
3. Use `answer`, `sources`, `tool_used`, and `confidence` from the response.
4. Do not improvise outside Brain OS data if the endpoint returns a result.

## Query Examples
```bash
curl -sS "$API_BASE/brain/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"query":"status CPP","user_id":"donna","role":"admin","channel":"telegram"}' | jq

curl -sS "$API_BASE/brain/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"query":"vendor printing","user_id":"donna","role":"admin","channel":"telegram"}' | jq

curl -sS "$API_BASE/brain/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"query":"weekly executive report","user_id":"donna","role":"admin","channel":"telegram"}' | jq
```

## Expected Response Shape
- `intent`
- `tool_used`
- `cache`
- `entities`
- `answer`
- `sources`
- `confidence`

## Fallback Raw Endpoints
- `/get_project`
- `/search_db`
- `/search_wiki`
- `/search_evidence`
- `/get_vendor`
- `/get_budget`
- `/get_action_items`
- `/generate_report`
