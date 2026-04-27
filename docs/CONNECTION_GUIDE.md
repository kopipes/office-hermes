# Agent VPS Connection Guide

All external agents must connect via MCP API only.

## Example
```yaml
provaliant_brain:
  type: mcp
  endpoint: "https://brain.provaliant.internal"
  api_key_env: "PROVALIANT_BRAIN_API_KEY"
  timeout_seconds: 30
  tools:
    - search_db
    - search_wiki
    - search_evidence
    - get_project
    - get_vendor
    - get_budget
    - get_action_items
    - generate_report
```
