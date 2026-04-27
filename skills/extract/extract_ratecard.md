# Skill: extract_ratecard

## Purpose
Extract vendor pricing into structured ratecard JSON.

## Output JSON
```json
{
  "vendor_name": null,
  "item_name": null,
  "item_category": null,
  "unit": null,
  "internal_price": null,
  "external_price": null,
  "minimum_order": null,
  "lead_time_days": null,
  "valid_from": null,
  "valid_until": null,
  "project": null,
  "source_reference": null,
  "approval_status": "pending_review",
  "confidence": 0.0,
  "missing_fields": []
}
```

## Extraction Notes
- convert shorthand currency (`45jt` => `45000000`)
- if one price only, map to `internal_price` unless explicitly marked selling/external
- infer item category from item name if possible
- never auto-approve
