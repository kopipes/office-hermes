# Provaliant Brain OS Ingest Skill

## Purpose
Convert manager/staff input from Telegram, WhatsApp, Discord, or manual chat into structured Provaliant Brain OS records.

This skill handles:
- meeting notes
- vendor quotes
- budgets
- project updates
- client/contact entries

## Core Rule
Do not store vague raw text only. Always classify, extract, validate, and write structured data through MCP.

## Input Commands
- `/entry meeting`
- `/entry vendor_quote`
- `/entry budget`
- `/entry project_update`
- `/entry contact`

## Workflow
1. Read raw user message.
2. Detect entry type.
3. Extract entities:
   - project
   - client
   - vendor
   - person
   - business unit
4. Extract structured fields.
5. Assign confidentiality:
   - vendor quotes, budgets, margins = confidential
   - general project update = internal
   - legal/IP sensitive = restricted
6. If confidence `< 0.85`, ask for confirmation.
7. If confidence `>= 0.85`, call MCP endpoint `/ingest`.
8. Return concise confirmation.
9. Never publish to wiki directly. Wiki update must be draft only.

## Entry Type Classification
### meeting
Keywords:
meeting, MOM, notulen, rapat, decision, action item, discussed, agreed

### vendor_quote
Keywords:
vendor, quote, quotation, harga, penawaran, lead time, produksi, booth, printing

### budget
Keywords:
budget, internal, external, margin, profit, cost, realisasi, RAB

### project_update
Keywords:
status, update, blocker, issue, delay, risk, next step

### contact
Keywords:
contact, PIC, phone, email, WhatsApp, client person

## Output Format
Always respond:
Detected:
- Type:
- Project:
- Client:
- Vendor:
- Key data:
- Confidence:
- Status:
Saved / Needs confirmation / Failed

## Confirmation Rule
If missing project, vendor, price, owner, or due date, ask one short clarification.

## MCP Tool
Call:
`POST /ingest`

Payload:
```json
{
  "user_id": "...",
  "role": "...",
  "channel": "...",
  "raw_text": "...",
  "entry_type": "...",
  "extracted": {},
  "confidence": 0.0
}
```

## Safety
- Do not overwrite approved budgets.
- Do not approve ratecards automatically.
- Do not publish wiki pages automatically.
- Do not expose confidential fields to unauthorized users.
- Always log writes.
