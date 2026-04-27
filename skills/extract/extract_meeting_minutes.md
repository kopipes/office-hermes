# Skill: extract_meeting_minutes

## Purpose
Convert raw MOM/transcript into structured meeting, decisions, and action items.

## Output JSON
```json
{
  "meeting": {
    "meeting_title": null,
    "meeting_date": null,
    "client": null,
    "project": null,
    "business_unit": null,
    "attendees": [],
    "summary": null
  },
  "decisions": [
    {
      "decision_text": null,
      "decision_owner": null,
      "impact": null,
      "confidence": 0.0
    }
  ],
  "action_items": [
    {
      "owner": null,
      "task_text": null,
      "due_date": null,
      "priority": "low | medium | high | urgent",
      "status": "open"
    }
  ],
  "risks": [],
  "related_files": [],
  "missing_fields": []
}
```

## Rules
- normalize relative deadlines (tomorrow/friday) to ISO date in WIB
- if owner unclear, set owner null and include in `missing_fields`
