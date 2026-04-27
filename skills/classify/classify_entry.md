# Skill: classify_entry

## Purpose
Classify raw operational input from WhatsApp/Telegram/Discord/ClickUp/web/API.

## Input
- raw_text
- source metadata (channel, sender, timestamp)

## Output JSON
```json
{
  "entry_type": "project_update | meeting | vendor_quote | ratecard | budget | client_contact | proposal | design_link | decision | action_item | issue | unknown",
  "detected_entities": [],
  "project": null,
  "client": null,
  "vendor": null,
  "business_unit": null,
  "confidentiality": "public | internal | confidential | restricted",
  "next_skill": "extract_project_status | extract_meeting_minutes | extract_ratecard | extract_budget | extract_client_profile",
  "confidence": 0.0,
  "needs_confirmation": true,
  "missing_fields": []
}
```

## Rules
- budget/ratecard/vendor pricing/margin/negotiation -> default `confidential`
- unreleased legal/IP -> default `restricted`
- confidence < 0.85 -> `needs_confirmation=true`
- if project missing -> ask project confirmation
