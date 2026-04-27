# Skill: query_router

## Purpose
Classify user query and choose the fastest safe retrieval path.

## Input
- raw_query
- user_id
- role
- channel
- optional context: project/client/vendor

## Output JSON
```json
{
  "query_type": "structured_operational | wiki_truth | evidence_lookup | relationship_context | report_generation",
  "primary_tool": "search_db | search_wiki | search_evidence | get_project | get_vendor | get_budget | get_action_items | generate_report",
  "secondary_tools": [],
  "filters": {
    "project": null,
    "client": null,
    "vendor": null,
    "business_unit": null,
    "date_range": null,
    "confidentiality_max": "internal"
  },
  "max_rows": 10,
  "max_chunks": 10,
  "needs_clarification": false,
  "confidence": 0.0
}
```

## Routing Rules
- status/budget/vendor/contact/project/task -> `structured_operational`
- SOP/policy/approved process -> `wiki_truth`
- "what did they say", "last discussion", "from meeting" -> `evidence_lookup`
- history/pattern/relationship/recurring issue -> `relationship_context`
- report/weekly/monthly/variance/dashboard -> `report_generation`

## Constraints
- default cap: max 10 rows + 10 chunks
- prefer SQL before semantic retrieval
- ask clarification if project/entity ambiguous
