# Skill: upsert_ratecard

## Purpose
Write/update vendor and ratecard data into Postgres via MCP.

## Input
- structured payload from `extract_ratecard`

## Behavior
1. find or create vendor entity
2. find or create vendor row
3. insert ratecard with `approval_status=pending_review`
4. link project if present
5. write audit log
6. return summary

## Output
```json
{
  "status": "saved | needs_confirmation | failed",
  "vendor_id": null,
  "ratecard_id": null,
  "summary": null,
  "next_action": null
}
```
