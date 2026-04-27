# Security Guide

- Expose only MCP API endpoint.
- Never expose Postgres directly to public internet.
- Enforce role-aware filtering in API and DB (RLS).
- Log all reads (`query_logs`) and writes (`audit_logs`).
- Keep confidential/restricted data access limited by role.
- Require human approval for destructive actions and wiki publishing.
