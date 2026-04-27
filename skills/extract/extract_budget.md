# Skill: extract_budget

## Purpose
Extract budget header and line items from text/table content.

## Output JSON
```json
{
  "project": null,
  "budget_version": null,
  "budget_status": "draft | pending_review | approved",
  "items": [
    {
      "item_category": null,
      "item_name": null,
      "qty": null,
      "unit": null,
      "unit_cost": null,
      "internal_total": null,
      "external_total": null,
      "profit": null,
      "profit_percent": null,
      "vendor": null,
      "notes": null
    }
  ],
  "totals": {
    "total_internal": null,
    "total_external": null,
    "total_profit": null,
    "profit_percent": null
  },
  "confidence": 0.0,
  "missing_fields": []
}
```

## Rules
- calculate missing totals when possible
- flag items with `profit_percent < 20`
- do not overwrite approved budget without explicit approval
