# Provaliant Brain OS
## Product Requirements Document, Implementation Plan, Step-by-Step Build Guide, and Prompt Library

Version: 1.0  
Owner: Chandra Sugiono / Provaliant Group  
System: Donna / Hermes Agent / OpenClaw  
Core Principle: Database-first, wiki-approved, skill-orchestrated, manager-accessible knowledge operating system.

---

# 1. Executive Summary

Provaliant Brain OS is a multi-user, operational second brain for Provaliant Group. It is designed to allow managers, directors, supervisors, and staff to enter, retrieve, analyze, and report company knowledge quickly through WhatsApp, Telegram, Discord, ClickUp, web wiki, and dashboards.

This system combines:

1. Karpathy-style Wiki  
   Human-readable, Git-versioned, approved operational knowledge.

2. Open Brain-style Semantic Memory  
   Postgres + pgvector + chunks + embeddings for raw evidence and semantic discovery.

3. GBrain-style Relationship Layer  
   Entity and relationship memory across projects, clients, vendors, people, budgets, and meetings.

4. Donna/Hermes/OpenClaw Orchestration  
   Skills replace external automation tools. No n8n dependency.

5. Structured Operational Database  
   Postgres is the truth layer for projects, vendors, budgets, contacts, ratecards, action items, KPIs, reports, and permissions.

The goal is not to let an LLM read all documents. The goal is to make the database filter, the wiki clarify, GBrain connect, and the LLM synthesize only a small, relevant context.

---

# 2. Problem Statement

Provaliant operates across multiple business units, including events, retail, licensing, IP, merchandise, creative, finance, operations, commerce, and partnerships. Important knowledge is distributed across WhatsApp groups, Telegram chats, Google Drive files, proposals, spreadsheets, PM Provaliant, meeting notes, budgets, ratecards, client contacts, vendor histories, and past designs.

Current pain points:

- Information is scattered across chat, Drive, personal memory, and documents.
- Managers cannot quickly find the latest project status, approved budget, ratecard, vendor comparison, or MOM.
- Repeated decisions are lost or buried in chat.
- The same vendor, client, project, or budget item may appear in many formats.
- LLM-based retrieval becomes slow and unreliable if it tries to read everything.
- Multi-user entry needs structure, permissions, and audit logs.
- Reports need fast turnaround without manual compilation.

---

# 3. Product Vision

Build Provaliant Brain OS as the company’s operational nervous system.

It should allow a manager to ask:

- What is the latest status of CPP?
- What did we decide in the last Futurevast meeting?
- Who is the cheapest booth production vendor under Rp50 juta?
- Which projects are over budget?
- Which clients have not been followed up this week?
- What are the open action items by BU?
- Generate a weekly management report.
- Show all proposals sent to malls in Q1.
- Find past designs for Disney or Marvel activation.
- Show approved purchasing ratecards.

And get answers quickly, with source links, permissions, and confidence.

---

# 4. Core Product Principles

## 4.1 Database Does Filtering, LLM Does Thinking

The LLM should not ingest all data into its prompt. It should receive only:

- 5 relevant wiki pages
- 10 relevant database rows
- 10 relevant evidence chunks
- selected GBrain relationships

## 4.2 Wiki Is Truth, Open Brain Is Memory

- Wiki = approved, human-readable truth.
- Postgres = structured operational truth.
- pgvector chunks = raw evidence memory.
- GBrain = relationship and context layer.
- Donna = orchestrator and interface.

## 4.3 Structured Entry First

Raw WhatsApp/Telegram ingestion is useful, but the system must push users toward structured entries:

- Project Update Entry
- Meeting Entry
- Budget Entry
- Vendor Entry
- Ratecard Entry
- Client Contact Entry
- Design/Brief Entry
- Proposal Entry

## 4.4 Skills Replace External Workflow Tools

No n8n dependency. Hermes/OpenClaw skills perform the workflow:

Trigger → Skill → Skill → Skill → Database → Wiki Draft → Notification

## 4.5 Every Important Answer Must Have a Source

Donna should answer with:

- Answer
- Source
- Last updated
- Confidence
- Related links
- Suggested next action

---

# 5. Users and Roles

## 5.1 User Roles

### Founder / CEO
Full access to all data, including restricted and confidential records.

### Director
Access to all business units relevant to their function. May access finance, operations, commerce, or creative data depending on permission.

### Business Unit Head / GM
Access to own BU projects, budgets, vendors, contacts, reports, and team data.

### Manager
Access to assigned projects, project budgets, meeting notes, action items, client contacts, and vendor records.

### Supervisor
Can enter updates, MOMs, action items, vendor quotes, operational reports, and project status.

### Staff
Can enter assigned data and view limited project/task information.

### Donna / System Agent
System-level read/write according to strict rules, with approval required for publishing wiki pages, external communication, destructive changes, or restricted knowledge.

---

# 6. Access and Permissions

## 6.1 Data Classification

1. Public  
   Website, public company profile, public case studies.

2. Internal  
   SOPs, project summaries, internal reports, general meeting notes.

3. Confidential  
   Budgets, ratecards, margins, vendor prices, client negotiations, contracts.

4. Restricted  
   Sensitive IP documents, legal disputes, unreleased licensing discussions, high-risk financial/legal files.

## 6.2 Permission Model

Postgres should use row-level security or equivalent application-level filtering.

Rules:

- Staff cannot see financial margins unless explicitly permitted.
- Managers see only assigned projects or BU data.
- Directors see function-wide data.
- Finance sees budget, AR, payment, and cost data.
- Operations sees vendor, procurement, production, logistics, and delivery data.
- Creative sees creative briefs, design files, style guides, and approvals.
- Chandra and Donna have full access, except restricted actions still require human approval.

---

# 7. Scope

## 7.1 In Scope

- Multi-user data entry through chat and web forms.
- WhatsApp, Telegram, Discord, ClickUp commands.
- Google Drive sync.
- PM Provaliant API sync.
- Project status tracking.
- Client/contact data.
- Vendor/ratecard data.
- Budget analysis.
- MOM extraction.
- Decision and action item tracking.
- Proposal and brief archive.
- Design link archive.
- Wiki generation and approval workflow.
- Fast query routing.
- Manager dashboards.
- Report generation.
- Audit logs.

## 7.2 Out of Scope for Phase 1

- Fully automated financial transactions.
- External client communication without approval.
- Full HR performance automation.
- Legal contract signing.
- Replacing PM Provaliant.
- Replacing Google Drive as file storage.

---

# 8. System Architecture

## 8.1 High-Level Architecture

```text
INPUTS
WhatsApp / Telegram / Discord / ClickUp / GDrive / PM Provaliant API / Website / Manual Entry

↓

DONNA INTAKE ROUTER
Classifies the entry and routes it to skills.

↓

HERMES SKILLS WORKFLOW LAYER
Intake skills, classification skills, extraction skills, database skills, wiki skills, GBrain skills, report skills.

↓

POSTGRES + PGVECTOR
Structured truth + semantic evidence memory.

↓

GBRAIN RELATIONSHIP LAYER
Entity and relationship graph across clients, projects, vendors, people, budgets, meetings, and files.

↓

KARPATHY-STYLE WIKI
Approved, human-readable Markdown knowledge.

↓

MCP QUERY SERVER
Exposes search_wiki, search_db, search_evidence, get_entity, generate_report.

↓

INTERFACES
WhatsApp / Telegram / Discord / ClickUp / Web Wiki / Manager Dashboard
```

---

# 9. Database Design

## 9.1 Core Tables

### users
```sql
users (
  id uuid primary key,
  full_name text,
  email text,
  phone text,
  telegram_id text,
  whatsapp_id text,
  role_id uuid,
  business_unit_id uuid,
  status text,
  created_at timestamptz,
  updated_at timestamptz
)
```

### roles
```sql
roles (
  id uuid primary key,
  role_name text,
  access_level text,
  permissions jsonb,
  created_at timestamptz
)
```

### business_units
```sql
business_units (
  id uuid primary key,
  name text,
  corporate_group text,
  director_id uuid,
  bu_head_id uuid,
  description text,
  status text
)
```

### entities
```sql
entities (
  id uuid primary key,
  entity_type text,
  name text,
  display_name text,
  aliases text[],
  description text,
  metadata jsonb,
  created_at timestamptz,
  updated_at timestamptz,
  unique(entity_type, name)
)
```

Entity types:

- client
- mall
- brand
- IP
- partner
- vendor
- person
- project
- business_unit
- document

---

## 9.2 Source and Document Tables

### sources
```sql
sources (
  id uuid primary key,
  source_type text,
  source_name text,
  channel_name text,
  group_name text,
  sender_name text,
  sender_identifier text,
  raw_reference text,
  imported_at timestamptz,
  metadata jsonb
)
```

### documents
```sql
documents (
  id uuid primary key,
  source_id uuid references sources(id),
  document_type text,
  title text,
  original_filename text,
  source_path text,
  gdrive_url text,
  project_id uuid,
  client_id uuid,
  business_unit_id uuid,
  owner_id uuid,
  confidentiality text,
  status text,
  effective_date date,
  checksum text unique,
  metadata jsonb,
  created_at timestamptz,
  imported_at timestamptz
)
```

Document types:

- proposal
- budget
- MOM
- design
- contract
- brief
- ratecard
- invoice
- project_report
- SOP
- client_profile
- vendor_profile

### chunks
```sql
chunks (
  id uuid primary key,
  document_id uuid references documents(id) on delete cascade,
  chunk_index int,
  content text,
  content_hash text,
  embedding vector(1536),
  page_number int,
  section_title text,
  created_at timestamptz,
  unique(document_id, chunk_index)
)
```

---

## 9.3 Project Tables

### projects
```sql
projects (
  id uuid primary key,
  project_code text unique,
  project_name text,
  client_id uuid,
  business_unit_id uuid,
  project_owner_id uuid,
  project_manager_id uuid,
  pm_provaliant_id text,
  status text,
  start_date date,
  end_date date,
  budget_total numeric,
  actual_cost numeric,
  revenue numeric,
  gross_margin numeric,
  gross_margin_percent numeric,
  risk_level text,
  gdrive_folder_url text,
  latest_summary text,
  last_updated timestamptz,
  created_at timestamptz
)
```

### project_updates
```sql
project_updates (
  id uuid primary key,
  project_id uuid references projects(id),
  update_date timestamptz,
  update_type text,
  status text,
  summary text,
  blockers text,
  next_steps text,
  submitted_by uuid,
  source_id uuid,
  confidence numeric,
  created_at timestamptz
)
```

---

## 9.4 Client and Contact Tables

### clients
```sql
clients (
  id uuid primary key,
  entity_id uuid references entities(id),
  client_type text,
  industry text,
  tier text,
  account_owner_id uuid,
  relationship_status text,
  last_contact_date date,
  next_followup_date date,
  notes text,
  metadata jsonb
)
```

### contacts
```sql
contacts (
  id uuid primary key,
  entity_id uuid references entities(id),
  client_id uuid references clients(id),
  full_name text,
  position text,
  company text,
  phone text,
  email text,
  whatsapp text,
  telegram text,
  relationship_owner_id uuid,
  notes text,
  confidentiality text,
  created_at timestamptz,
  updated_at timestamptz
)
```

---

## 9.5 Vendor and Ratecard Tables

### vendors
```sql
vendors (
  id uuid primary key,
  entity_id uuid references entities(id),
  vendor_category text,
  service_area text,
  contact_person text,
  phone text,
  email text,
  reliability_score numeric,
  quality_score numeric,
  speed_score numeric,
  payment_terms text,
  blacklist_flag boolean default false,
  notes text,
  created_at timestamptz,
  updated_at timestamptz
)
```

### ratecards
```sql
ratecards (
  id uuid primary key,
  vendor_id uuid references vendors(id),
  item_name text,
  item_category text,
  unit text,
  internal_price numeric,
  external_price numeric,
  minimum_order numeric,
  lead_time_days int,
  valid_from date,
  valid_until date,
  source_document_id uuid,
  approval_status text,
  created_by uuid,
  approved_by uuid,
  approved_at timestamptz,
  created_at timestamptz
)
```

---

## 9.6 Budget Tables

### budgets
```sql
budgets (
  id uuid primary key,
  project_id uuid references projects(id),
  budget_version text,
  budget_status text,
  total_internal numeric,
  total_external numeric,
  total_profit numeric,
  profit_percent numeric,
  source_document_id uuid,
  created_by uuid,
  approved_by uuid,
  approved_at timestamptz,
  created_at timestamptz
)
```

### budget_items
```sql
budget_items (
  id uuid primary key,
  budget_id uuid references budgets(id),
  item_category text,
  item_name text,
  qty numeric,
  unit text,
  unit_cost numeric,
  internal_total numeric,
  external_total numeric,
  profit numeric,
  profit_percent numeric,
  vendor_id uuid,
  notes text,
  created_at timestamptz
)
```

---

## 9.7 Meeting, Decision, and Task Tables

### meetings
```sql
meetings (
  id uuid primary key,
  meeting_title text,
  meeting_date timestamptz,
  client_id uuid,
  project_id uuid,
  business_unit_id uuid,
  attendees text[],
  source_document_id uuid,
  summary text,
  created_by uuid,
  created_at timestamptz
)
```

### decisions
```sql
decisions (
  id uuid primary key,
  meeting_id uuid references meetings(id),
  project_id uuid references projects(id),
  decision_text text,
  decision_owner_id uuid,
  decision_date date,
  impact text,
  confidence numeric,
  source_document_id uuid,
  created_at timestamptz
)
```

### action_items
```sql
action_items (
  id uuid primary key,
  meeting_id uuid,
  project_id uuid,
  owner_id uuid,
  task_text text,
  due_date date,
  status text,
  priority text,
  source_id uuid,
  created_by uuid,
  created_at timestamptz,
  updated_at timestamptz
)
```

---

## 9.8 Wiki Tables

### wiki_pages
```sql
wiki_pages (
  id uuid primary key,
  slug text unique,
  title text,
  category text,
  content text,
  summary text,
  owner_id uuid,
  approval_status text,
  source_document_ids uuid[],
  related_entity_ids uuid[],
  freshness_rule text,
  last_reviewed_at timestamptz,
  embedding vector(1536),
  version int,
  created_at timestamptz,
  updated_at timestamptz
)
```

### wiki_change_requests
```sql
wiki_change_requests (
  id uuid primary key,
  wiki_page_id uuid,
  proposed_content text,
  change_reason text,
  proposed_by uuid,
  approval_status text,
  reviewed_by uuid,
  reviewed_at timestamptz,
  created_at timestamptz
)
```

---

## 9.9 Reporting and Audit Tables

### reports
```sql
reports (
  id uuid primary key,
  report_type text,
  title text,
  period_start date,
  period_end date,
  business_unit_id uuid,
  generated_by uuid,
  content text,
  source_refs jsonb,
  created_at timestamptz
)
```

### query_logs
```sql
query_logs (
  id uuid primary key,
  user_id uuid,
  query_text text,
  query_type text,
  tools_used text[],
  rows_returned int,
  chunks_returned int,
  response_summary text,
  created_at timestamptz
)
```

### audit_logs
```sql
audit_logs (
  id uuid primary key,
  user_id uuid,
  action_type text,
  table_name text,
  record_id uuid,
  previous_value jsonb,
  new_value jsonb,
  created_at timestamptz
)
```

---

# 10. Indexing Strategy

Use indexes for speed.

```sql
create index idx_projects_status on projects(status);
create index idx_projects_bu on projects(business_unit_id);
create index idx_projects_client on projects(client_id);
create index idx_documents_type on documents(document_type);
create index idx_documents_project on documents(project_id);
create index idx_documents_client on documents(client_id);
create index idx_documents_confidentiality on documents(confidentiality);
create index idx_ratecards_vendor on ratecards(vendor_id);
create index idx_ratecards_category on ratecards(item_category);
create index idx_budget_items_budget on budget_items(budget_id);
create index idx_action_items_owner on action_items(owner_id);
create index idx_action_items_status on action_items(status);
create index idx_meetings_project on meetings(project_id);
create index idx_wiki_category on wiki_pages(category);
create index idx_wiki_approval on wiki_pages(approval_status);
```

Vector indexes:

```sql
create index idx_chunks_embedding on chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index idx_wiki_embedding on wiki_pages using ivfflat (embedding vector_cosine_ops) with (lists = 100);
```

---

# 11. Skills Architecture

## 11.1 Skill Folder Structure

```text
skills/
├── intake/
│   ├── whatsapp_intake.md
│   ├── telegram_intake.md
│   ├── discord_intake.md
│   ├── clickup_intake.md
│   ├── gdrive_sync.md
│   └── pm_provaliant_api_sync.md
├── classify/
│   ├── classify_entry.md
│   ├── detect_entity.md
│   ├── detect_document_type.md
│   ├── detect_confidentiality.md
│   └── detect_business_unit.md
├── extract/
│   ├── extract_budget.md
│   ├── extract_ratecard.md
│   ├── extract_meeting_minutes.md
│   ├── extract_action_items.md
│   ├── extract_decisions.md
│   ├── extract_project_status.md
│   ├── extract_client_profile.md
│   └── extract_drive_links.md
├── db/
│   ├── upsert_project.md
│   ├── upsert_client.md
│   ├── upsert_vendor.md
│   ├── upsert_budget.md
│   ├── upsert_ratecard.md
│   ├── upsert_meeting.md
│   ├── upsert_decision.md
│   └── upsert_action_item.md
├── wiki/
│   ├── generate_wiki_draft.md
│   ├── update_project_wiki.md
│   ├── update_vendor_wiki.md
│   ├── update_client_wiki.md
│   ├── submit_wiki_for_approval.md
│   └── publish_approved_wiki.md
├── gbrain/
│   ├── gbrain_entity_link.md
│   ├── gbrain_relationship_update.md
│   ├── gbrain_context_lookup.md
│   └── gbrain_pattern_discovery.md
├── query/
│   ├── query_router.md
│   ├── sql_query.md
│   ├── wiki_search.md
│   ├── semantic_search.md
│   ├── evidence_search.md
│   └── hybrid_answer.md
└── reports/
    ├── daily_manager_brief.md
    ├── weekly_project_report.md
    ├── budget_variance_report.md
    ├── vendor_comparison_report.md
    ├── project_health_report.md
    ├── client_status_report.md
    └── kpi_report.md
```

---

# 12. Query Router Logic

Donna should classify every query into one of these types.

## 12.1 Query Types

### structured_operational
Examples:

- Show active projects.
- Which projects are over budget?
- Who owns CPP?
- What is the margin for SNP?

Route:

```text
SQL only → summarize
```

### wiki_truth
Examples:

- What is the procurement SOP?
- What is the budget approval flow?
- What is the approved client follow-up process?

Route:

```text
Wiki search → approved pages only → answer
```

### evidence_lookup
Examples:

- What did the client say about the design revision?
- Find the WhatsApp discussion about vendor ABC.
- What was mentioned in the last meeting?

Route:

```text
Semantic search chunks → filter by entity/project/date → answer with evidence
```

### relationship_context
Examples:

- What is the history of this vendor?
- Which projects involved Futurevast and retail?
- What patterns caused project delay?

Route:

```text
GBrain relationship lookup → SQL → evidence chunks → answer
```

### report_generation
Examples:

- Generate weekly management report.
- Prepare budget variance analysis.
- Summarize project health.

Route:

```text
SQL + wiki + evidence + GBrain → report skill
```

---

# 13. Ingestion Workflows

## 13.1 WhatsApp / Telegram Entry Flow

```text
User sends message
→ intake skill captures message
→ classify_entry
→ detect entity/project/client/vendor
→ extract structured fields
→ confidence check
→ if confidence < 0.85, ask confirmation
→ upsert into Postgres
→ link in GBrain
→ create wiki draft if important
→ notify user
```

## 13.2 Google Drive Sync Flow

```text
New file detected
→ gdrive_sync
→ document classifier
→ extract text/OCR if needed
→ metadata extraction
→ chunking
→ embedding
→ documents/chunks insert
→ entity linking
→ wiki draft suggestion
```

## 13.3 PM Provaliant API Flow

```text
Scheduled sync
→ fetch projects/tasks/status/budget
→ normalize fields
→ upsert projects/action_items/budgets
→ detect changes
→ notify owners if risk or delay
```

## 13.4 Meeting MOM Flow

```text
MOM uploaded or pasted
→ extract meeting date, attendees, project, client
→ extract decisions
→ extract action items
→ insert meeting, decisions, action_items
→ update project latest summary
→ suggest wiki update
```

---

# 14. Web Wiki Structure

```text
wiki/
├── company/
│   ├── overview.md
│   ├── operating-system.md
│   └── glossary.md
├── clients/
│   ├── malls/
│   ├── brands/
│   ├── ip-owners/
│   └── corporate/
├── projects/
│   ├── active/
│   ├── completed/
│   └── archive/
├── finance/
│   ├── budget-approval-flow.md
│   ├── margin-guardrails.md
│   ├── purchasing-ratecards.md
│   └── budget-templates.md
├── vendors/
│   ├── production/
│   ├── printing/
│   ├── merchandise/
│   ├── logistics/
│   └── talent/
├── meetings/
│   ├── management/
│   ├── client-meetings/
│   └── decision-log.md
├── sops/
│   ├── procurement.md
│   ├── proposal.md
│   ├── project-kickoff.md
│   ├── project-closing.md
│   └── client-followup.md
├── ip-library/
│   ├── disney.md
│   ├── marvel.md
│   ├── sanrio.md
│   ├── pokemon.md
│   ├── legenda-panji.md
│   └── dino-island.md
└── reports/
    ├── weekly/
    ├── monthly/
    └── quarterly/
```

---

# 15. Dashboard Requirements

## 15.1 Founder Dashboard

Widgets:

- Revenue by BU
- Gross margin by BU
- Projects at risk
- Budget variance
- AR aging
- Open action items
- Top client follow-ups
- Vendor issues
- Weekly decisions
- Cross-BU opportunities

## 15.2 Director Dashboard

By function:

Finance:

- Budget vs actual
- Margin guardrails
- AR days
- Payment status
- Cost anomalies

Operations:

- Vendor SLA
- Procurement lead time
- On-time/on-budget projects
- Logistics blockers
- Production risks

Commerce:

- Pipeline
- Proposal status
- New clients
- Cross-sell opportunities
- Client retention

Creative:

- Creative backlog
- Design approval rate
- Revision rate
- On-time delivery
- IP/format innovation

## 15.3 Manager Dashboard

- Assigned projects
- Project status
- Open tasks
- Budget status
- MOMs
- Vendor contacts
- Pending approvals
- Drive links

---

# 16. Commands for Managers

## 16.1 Entry Commands

```text
/entry project_update
/entry meeting
/entry budget
/entry vendor_quote
/entry ratecard
/entry client_contact
/entry proposal
/entry design_link
/entry issue
/entry decision
```

## 16.2 Query Commands

```text
/status [project]
/vendor compare [category]
/budget [project]
/mom [project/client]
/tasks [owner/project]
/contact [client]
/wiki [topic]
/report weekly
/report budget_variance
/report project_health
```

---

# 17. Implementation Plan

## Phase 0 — Alignment and Decisions

Goal: confirm architecture and lock principles.

Tasks:

1. Confirm no n8n.
2. Confirm Hermes Skills as workflow layer.
3. Confirm Postgres + pgvector as main DB.
4. Confirm Wiki + GBrain separation.
5. Confirm source systems:
   - WhatsApp
   - Telegram
   - Discord/ClickUp
   - Google Drive
   - PM Provaliant API
   - Website
6. Confirm first user roles.
7. Confirm first business units.
8. Confirm data classification.

Output:

- Approved architecture.
- Approved scope.
- Approved Phase 1 build list.

---

## Phase 1 — Database Foundation

Goal: create the structured truth layer.

Tasks:

1. Provision Postgres + pgvector.
2. Create schema.
3. Create indexes.
4. Create roles and permissions.
5. Create initial business units.
6. Create initial users.
7. Create entity seed list:
   - Clients
   - Vendors
   - IPs
   - Projects
   - People
8. Create migration scripts.
9. Create backup scripts.
10. Test simple queries.

Success criteria:

- DB is live.
- Core tables exist.
- Basic SQL queries return fast.
- Initial users and roles are seeded.

---

## Phase 2 — MCP Server

Goal: expose safe tools for Donna/OpenClaw.

MCP tools:

```text
search_db
search_wiki
search_evidence
get_project
get_vendor
get_client
get_budget
get_ratecard
get_meeting
get_action_items
generate_report
suggest_wiki_update
```

Tasks:

1. Build FastAPI MCP server.
2. Add DB connection.
3. Add permission filters.
4. Add query logging.
5. Add tool definitions.
6. Test with Donna/OpenClaw.

Success criteria:

- Donna can query Postgres safely.
- Results are permission-filtered.
- Query logs are saved.

---

## Phase 3 — Skills Workflow Layer

Goal: create internal workflows using Hermes/OpenClaw skills.

Build first 12 skills:

1. classify_entry
2. detect_entity
3. extract_project_status
4. extract_meeting_minutes
5. extract_action_items
6. extract_decisions
7. extract_budget
8. extract_ratecard
9. upsert_project
10. upsert_vendor
11. upsert_budget
12. query_router

Success criteria:

- Chat entry can become structured DB record.
- Meeting notes can produce decisions and action items.
- Vendor quote can become pending ratecard.
- Query router chooses SQL/wiki/evidence correctly.

---

## Phase 4 — Google Drive and Document Ingestion

Goal: ingest files without making Google Drive the brain.

Tasks:

1. Create Drive folder map.
2. Build gdrive_sync skill.
3. Extract metadata.
4. Parse PDF/DOCX/XLSX.
5. Chunk documents.
6. Generate embeddings.
7. Store documents/chunks.
8. Link to projects/entities.
9. Create wiki draft suggestions.

Success criteria:

- New Drive files are indexed.
- Files are searchable by project/client/vendor.
- Source links are preserved.

---

## Phase 5 — Chat Interfaces

Goal: let managers enter and query through WhatsApp/Telegram.

Tasks:

1. Define command syntax.
2. Build WhatsApp command handler.
3. Build Telegram command handler.
4. Add confirmation workflow.
5. Add permission checks.
6. Add help menu.
7. Add error handling.

Success criteria:

- Manager can submit project update.
- Manager can submit MOM.
- Manager can query project status.
- Donna asks for confirmation when extraction is uncertain.

---

## Phase 6 — Wiki Layer

Goal: create approved human-readable brain.

Tasks:

1. Create wiki folder structure.
2. Create templates:
   - Project page
   - Client page
   - Vendor page
   - SOP page
   - Meeting page
   - Finance page
3. Create wiki draft generation skill.
4. Create approval workflow.
5. Publish approved pages.
6. Sync pages into wiki_pages table.
7. Embed wiki pages.

Success criteria:

- Wiki has approved pages.
- Wiki pages are searchable.
- Draft updates do not overwrite approved pages without approval.

---

## Phase 7 — GBrain Integration

Goal: use GBrain for relationships and context.

Tasks:

1. Map Postgres entities to GBrain nodes.
2. Create relationship types:
   - client_has_project
   - project_uses_vendor
   - project_has_budget
   - meeting_has_decision
   - person_owns_task
   - document_supports_project
   - IP_connected_to_client
3. Build GBrain sync skill.
4. Build context lookup skill.
5. Build pattern discovery skill.

Success criteria:

- Donna can answer relationship questions.
- GBrain enriches context but does not replace Postgres.

---

## Phase 8 — Reports and Dashboards

Goal: operational adoption.

Tasks:

1. Build report skills:
   - weekly_project_report
   - budget_variance_report
   - vendor_comparison_report
   - client_status_report
   - kpi_report
2. Build web dashboard.
3. Add role-based views.
4. Add export to PDF/Markdown.
5. Add scheduled reports via Hermes cron.

Success criteria:

- Weekly report generated in less than 1 minute.
- Managers see assigned projects.
- Directors see function dashboards.
- Founder sees group-level dashboard.

---

## Phase 9 — Governance and Optimization

Goal: make it reliable long-term.

Tasks:

1. Add audit logs.
2. Add stale page detection.
3. Add duplicate detection.
4. Add broken Drive link checker.
5. Add permission review.
6. Add data quality scoring.
7. Add performance benchmark.
8. Add backup/restore test.

Success criteria:

- System is trustworthy.
- Data quality improves over time.
- Queries stay fast.

---

# 18. Step-by-Step Build Instructions

## Step 1 — Create Repository

```bash
mkdir provaliant-brain-os
cd provaliant-brain-os
mkdir db mcp-server skills wiki raw dashboards scripts docs
```

## Step 2 — Create Database Files

```bash
mkdir db/migrations
mkdir db/seeds
mkdir db/backups
```

Create:

```text
db/schema.sql
db/indexes.sql
db/rls.sql
db/seeds/business_units.sql
db/seeds/roles.sql
db/seeds/users.sql
```

## Step 3 — Create Wiki Structure

```bash
mkdir -p wiki/{company,clients,projects,finance,vendors,meetings,sops,ip-library,reports}
mkdir -p wiki/projects/{active,completed,archive}
mkdir -p wiki/clients/{malls,brands,ip-owners,corporate}
mkdir -p wiki/vendors/{production,printing,merchandise,logistics,talent}
```

## Step 4 — Create Skills Structure

```bash
mkdir -p skills/{intake,classify,extract,db,wiki,gbrain,query,reports}
```

## Step 5 — Build Schema

Run schema in Postgres.

```bash
psql $DATABASE_URL -f db/schema.sql
psql $DATABASE_URL -f db/indexes.sql
psql $DATABASE_URL -f db/rls.sql
```

## Step 6 — Build MCP Server

Use FastAPI or Python MCP server.

Required endpoints/tools:

```text
/search_db
/search_wiki
/search_evidence
/get_project
/get_vendor
/get_budget
/get_action_items
/generate_report
```

## Step 7 — Build First Skills

Start with these:

```text
classify_entry
extract_project_status
extract_meeting_minutes
extract_ratecard
upsert_project
upsert_ratecard
query_router
sql_query
hybrid_answer
```

## Step 8 — Test Manual Entries

Test with:

```text
Vendor ABC quote booth 45jt, lead time 10 days, for CPP.
```

Expected result:

```text
Vendor created or matched.
Ratecard created as pending approval.
Project CPP linked.
Donna asks for confirmation if confidence is low.
```

## Step 9 — Test Query

Ask:

```text
Who is the cheapest booth vendor for CPP?
```

Expected:

```text
SQL query only.
No semantic search needed.
Fast answer.
```

## Step 10 — Add Drive Sync

Map folders:

```text
GDrive/Projects
GDrive/Clients
GDrive/Finance
GDrive/Proposals
GDrive/Designs
GDrive/MOM
GDrive/Vendors
```

## Step 11 — Add Wiki Approval

Raw source should create draft only.

```text
raw input → wiki draft → human approval → approved wiki
```

## Step 12 — Add Reports

First reports:

```text
Weekly Project Health
Budget Variance
Vendor Comparison
Action Items by Owner
Client Follow-Up Report
```

---

# 19. Acceptance Criteria

## Performance

- SQL structured queries: under 300ms for common queries.
- Wiki search: under 2 seconds.
- Semantic evidence search: under 3 seconds.
- Standard reports: under 60 seconds.

## Accuracy

- Structured extraction confidence above 85% for common entries.
- Low-confidence entries require confirmation.
- All important answers show source.

## Adoption

- Managers can enter updates from WhatsApp/Telegram.
- Directors can generate reports without asking admin.
- Founder can ask cross-BU questions.
- Wiki becomes trusted source of truth.

## Governance

- All writes are logged.
- All wiki changes require approval.
- Confidential records are permission-filtered.
- Restricted records are not exposed to normal users.

---

# 20. Prompt Library

## 20.1 Prompt to Ask ChatGPT to Review the PRD

```text
Act as a senior product architect and CTO. Review this PRD for Provaliant Brain OS. Identify missing requirements, weak assumptions, implementation risks, database gaps, permission risks, and operational adoption issues. Then propose improvements prioritized by impact and difficulty.
```

## 20.2 Prompt to Generate SQL Schema

```text
Using the Provaliant Brain OS PRD, generate a production-ready PostgreSQL schema with pgvector support. Include tables, primary keys, foreign keys, indexes, enum suggestions, JSONB fields where useful, created_at/updated_at timestamps, and comments explaining each table. Optimize for fast project, vendor, budget, meeting, action item, and wiki queries.
```

## 20.3 Prompt to Generate Row-Level Security

```text
Design row-level security policies for Provaliant Brain OS. Roles are Founder, Director, BU Head, Manager, Supervisor, Staff, and Donna Agent. Data classifications are Public, Internal, Confidential, and Restricted. Generate PostgreSQL RLS policies and explain which users can read/write each table.
```

## 20.4 Prompt to Generate MCP Server

```text
Generate a Python FastAPI MCP server for Provaliant Brain OS. It must expose tools: search_db, search_wiki, search_evidence, get_project, get_vendor, get_budget, get_action_items, generate_report, and suggest_wiki_update. It should connect to Postgres, enforce user permissions, log all queries, and return structured JSON results with source references.
```

## 20.5 Prompt to Generate Query Router Logic

```text
Design the query router for Donna in Provaliant Brain OS. The router must classify user questions into structured_operational, wiki_truth, evidence_lookup, relationship_context, or report_generation. For each type, specify which tools to call, what filters to apply, maximum rows/chunks to retrieve, and how Donna should synthesize the final answer.
```

## 20.6 Prompt to Generate Hermes Skill: classify_entry

```text
Create a Hermes/OpenClaw skill called classify_entry for Provaliant Brain OS. The skill receives raw text from WhatsApp, Telegram, Discord, ClickUp, web form, GDrive metadata, or PM Provaliant API. It must classify the entry type, detect possible project/client/vendor/person/entity, assign confidentiality level, estimate confidence, and output structured JSON for the next skill.
```

## 20.7 Prompt to Generate Hermes Skill: extract_ratecard

```text
Create a Hermes/OpenClaw skill called extract_ratecard. It receives raw text or document content containing vendor pricing. It must extract vendor name, item name, category, unit, internal price, external price, minimum order, lead time, validity period, source document, confidence score, and missing fields. It must output JSON ready for upsert_ratecard.
```

## 20.8 Prompt to Generate Hermes Skill: extract_meeting_minutes

```text
Create a Hermes/OpenClaw skill called extract_meeting_minutes. It receives meeting notes, transcript, or chat summary. It must extract meeting title, date, attendees, project, client, summary, decisions, action items, risks, owners, deadlines, and related files. Output structured JSON for meetings, decisions, and action_items tables.
```

## 20.9 Prompt to Generate Hermes Skill: extract_budget

```text
Create a Hermes/OpenClaw skill called extract_budget for Provaliant Brain OS. It receives spreadsheet text, PDF table text, or pasted budget data. It must extract project, budget version, item category, item name, quantity, unit, unit cost, internal total, external total, profit, profit percent, vendor, approval status, and source reference. Output normalized JSON for budgets and budget_items.
```

## 20.10 Prompt to Generate Wiki Templates

```text
Create Markdown wiki templates for Provaliant Brain OS for project pages, client pages, vendor pages, SOP pages, meeting pages, finance pages, IP pages, and report pages. Each template must include YAML frontmatter with slug, title, category, owner, approval_status, related_entities, source_documents, tags, freshness_rule, last_reviewed, and version.
```

## 20.11 Prompt to Generate Manager Dashboard Spec

```text
Design the manager dashboard for Provaliant Brain OS. Include screens, widgets, filters, permissions, data sources, and example SQL queries. The dashboard must show assigned projects, project health, budget status, open action items, MOMs, client contacts, vendor records, pending approvals, and Drive links.
```

## 20.12 Prompt to Generate Founder Dashboard Spec

```text
Design the founder dashboard for Provaliant Brain OS. Include widgets for revenue by BU, gross margin by BU, projects at risk, budget variance, AR aging, open action items, vendor issues, weekly decisions, client follow-ups, and cross-BU opportunities. Include data sources and SQL logic.
```

## 20.13 Prompt to Generate Report Skill

```text
Create a Hermes/OpenClaw report skill called weekly_project_report. It should query projects, project_updates, budgets, action_items, meetings, and GBrain context. It must produce a concise weekly report grouped by business unit with project status, risks, blockers, budget issues, decisions, and next actions.
```

## 20.14 Prompt to Generate Data Ingestion Test Cases

```text
Create 30 test cases for Provaliant Brain OS ingestion. Include WhatsApp messages, Telegram messages, meeting notes, vendor quotes, budget snippets, Drive file metadata, project updates, client contact updates, and ambiguous entries. For each test case, provide expected classification, extracted fields, confidence score, and database tables affected.
```

## 20.15 Prompt to Generate Operational SOP

```text
Write an SOP for Provaliant managers on how to use Provaliant Brain OS through WhatsApp, Telegram, and the web wiki. Include how to submit project updates, MOMs, vendor quotes, budgets, contacts, design links, and issues. Include command examples and what Donna will reply.
```

## 20.16 Prompt to Generate First 20 Manager Queries

```text
Generate the first 20 daily-use queries for Provaliant managers using Provaliant Brain OS. Group them by project status, budget, vendor, client, meeting, action item, wiki/SOP, and report generation. For each query, specify the expected data source and query route.
```

---

# 21. First 20 Manager Queries

1. What is the latest status of CPP?
2. What is the latest status of SNP?
3. Which projects are delayed this week?
4. Which projects are over budget?
5. Show all open action items assigned to me.
6. What did we decide in the last Futurevast meeting?
7. Show the latest MOM for Disney.
8. Who is the contact person for Senayan Park?
9. Compare booth production vendors under Rp50 juta.
10. Show approved ratecards for printing.
11. Which vendor has the best quality score for production?
12. Show budget variance for CPP.
13. Which project has margin below 20%?
14. Find past design links for Marvel activation.
15. Show proposals sent to malls this quarter.
16. What is the SOP for budget approval?
17. What is the SOP for vendor onboarding?
18. Generate weekly project health report.
19. Generate action item report by BU.
20. Generate client follow-up report.

---

# 22. First Build Priority

Build in this order:

1. Postgres schema
2. MCP server
3. query_router skill
4. classify_entry skill
5. extract_meeting_minutes skill
6. extract_ratecard skill
7. extract_budget skill
8. upsert database skills
9. WhatsApp/Telegram command handling
10. wiki draft/approval workflow
11. report skills
12. GBrain relationship enrichment
13. dashboards

---

# 23. Final Operating Model

Provaliant Brain OS should operate like this:

```text
People enter data through natural channels.
Skills structure the data.
Postgres stores the truth.
pgvector stores searchable evidence.
GBrain connects relationships.
Wiki stores approved knowledge.
MCP exposes safe tools.
Donna routes, answers, and reports.
Managers act faster.
```

The system should feel like a company brain, but behave like an operational database.

---

# 24. Deployable Build Pack

This section converts the PRD into an implementation-ready build pack.

---

## 24.1 Repository Layout

```text
provaliant-brain-os/
├── README.md
├── .env.example
├── docker-compose.yml
├── db/
│   ├── schema.sql
│   ├── indexes.sql
│   ├── rls.sql
│   ├── seeds/
│   │   ├── roles.sql
│   │   ├── business_units.sql
│   │   └── users.sql
│   └── migrations/
├── mcp-server/
│   ├── main.py
│   ├── requirements.txt
│   ├── auth.py
│   ├── db.py
│   ├── tools/
│   │   ├── search_db.py
│   │   ├── search_wiki.py
│   │   ├── search_evidence.py
│   │   ├── get_project.py
│   │   ├── get_vendor.py
│   │   ├── get_budget.py
│   │   ├── get_action_items.py
│   │   ├── generate_report.py
│   │   └── suggest_wiki_update.py
│   └── tests/
├── skills/
│   ├── intake/
│   ├── classify/
│   ├── extract/
│   ├── db/
│   ├── wiki/
│   ├── gbrain/
│   ├── query/
│   └── reports/
├── wiki/
│   ├── company/
│   ├── clients/
│   ├── projects/
│   ├── finance/
│   ├── vendors/
│   ├── meetings/
│   ├── sops/
│   ├── ip-library/
│   └── reports/
├── raw/
│   ├── whatsapp/
│   ├── telegram/
│   ├── gdrive/
│   └── api/
├── dashboards/
│   ├── founder_dashboard.md
│   ├── director_dashboard.md
│   └── manager_dashboard.md
├── scripts/
│   ├── install_brain_vps.sh
│   ├── setup_db.sh
│   ├── run_mcp.sh
│   ├── backup_db.sh
│   ├── restore_db.sh
│   └── health_check.sh
└── docs/
    ├── USER_GUIDE.md
    ├── INSTALLATION_GUIDE.md
    ├── CONNECTION_GUIDE.md
    ├── SECURITY_GUIDE.md
    └── TROUBLESHOOTING.md
```

---

# 25. Installation Scripts

## 25.1 `.env.example`

```bash
# Provaliant Brain OS Environment
APP_ENV=production
APP_NAME=provaliant-brain-os

# Database
POSTGRES_DB=provaliant_brain
POSTGRES_USER=brain_user
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://brain_user:CHANGE_ME_STRONG_PASSWORD@localhost:5432/provaliant_brain

# MCP
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_API_KEY=CHANGE_ME_SECRET_API_KEY

# Security
DEFAULT_CONFIDENTIALITY=internal
ENABLE_QUERY_LOGGING=true
ENABLE_AUDIT_LOGGING=true

# Embeddings
EMBEDDING_PROVIDER=openrouter
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Wiki
WIKI_PATH=/opt/provaliant-brain-os/wiki
RAW_PATH=/opt/provaliant-brain-os/raw

# Backups
BACKUP_PATH=/opt/provaliant-brain-os/backups
BACKUP_RETENTION_DAYS=30
```

---

## 25.2 `scripts/install_brain_vps.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Provaliant Brain OS VPS Installer ==="

sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  git curl wget unzip build-essential \
  python3 python3-pip python3-venv \
  postgresql postgresql-contrib postgresql-server-dev-all \
  nginx ufw jq

# Install pgvector
cd /tmp
if [ ! -d pgvector ]; then
  git clone https://github.com/pgvector/pgvector.git
fi
cd pgvector
make
sudo make install

# Create app directory
sudo mkdir -p /opt/provaliant-brain-os
sudo chown -R $USER:$USER /opt/provaliant-brain-os

# Firewall
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

echo "Installation complete. Next: clone repository into /opt/provaliant-brain-os and run setup_db.sh"
```

---

## 25.3 `scripts/setup_db.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

source .env

echo "=== Setting up Provaliant Brain OS database ==="

sudo -u postgres psql <<SQL
CREATE DATABASE ${POSTGRES_DB};
CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
SQL

sudo -u postgres psql -d ${POSTGRES_DB} <<SQL
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SQL

psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/indexes.sql
psql "$DATABASE_URL" -f db/rls.sql
psql "$DATABASE_URL" -f db/seeds/roles.sql
psql "$DATABASE_URL" -f db/seeds/business_units.sql

echo "Database setup complete."
```

---

## 25.4 `scripts/run_mcp.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

source .env
cd mcp-server

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --host ${MCP_HOST} --port ${MCP_PORT}
```

---

## 25.5 `scripts/backup_db.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

source .env
mkdir -p "$BACKUP_PATH"

TS=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_PATH/provaliant_brain_$TS.sql.gz"

pg_dump "$DATABASE_URL" | gzip > "$OUT"

find "$BACKUP_PATH" -type f -name "*.sql.gz" -mtime +${BACKUP_RETENTION_DAYS} -delete

echo "Backup created: $OUT"
```

---

## 25.6 `scripts/health_check.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

source .env

echo "Checking Postgres..."
pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT

echo "Checking MCP server..."
curl -s -H "Authorization: Bearer $MCP_API_KEY" http://localhost:${MCP_PORT}/health | jq .

echo "Checking core tables..."
psql "$DATABASE_URL" -c "select count(*) from projects;"
psql "$DATABASE_URL" -c "select count(*) from documents;"
psql "$DATABASE_URL" -c "select count(*) from wiki_pages;"

echo "Health check complete."
```

---

# 26. MCP Server Skeleton

## 26.1 `mcp-server/requirements.txt`

```text
fastapi==0.115.0
uvicorn==0.30.6
psycopg2-binary==2.9.9
pydantic==2.8.2
python-dotenv==1.0.1
```

---

## 26.2 `mcp-server/db.py`

```python
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def fetch_all(query: str, params: tuple = ()):  # returns list[dict]
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]


def fetch_one(query: str, params: tuple = ()):  # returns dict | None
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None


def execute(query: str, params: tuple = ()):  # returns affected rows
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount
```

---

## 26.3 `mcp-server/auth.py`

```python
import os
from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()

MCP_API_KEY = os.getenv("MCP_API_KEY")


def require_auth(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "").strip()
    if token != MCP_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return True
```

---

## 26.4 `mcp-server/main.py`

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from auth import require_auth
from db import fetch_all, fetch_one, execute

app = FastAPI(title="Provaliant Brain OS MCP Server")


class SearchRequest(BaseModel):
    query: str
    user_id: str | None = None
    role: str | None = None
    business_unit_id: str | None = None
    limit: int = 10


class ProjectRequest(BaseModel):
    project_code_or_name: str
    user_id: str | None = None
    role: str | None = None


@app.get("/health")
def health(_: bool = Depends(require_auth)):
    return {"status": "ok", "service": "provaliant-brain-os"}


@app.post("/search_db")
def search_db(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        SELECT project_code, project_name, status, latest_summary, risk_level, last_updated
        FROM projects
        WHERE project_name ILIKE %s OR project_code ILIKE %s OR latest_summary ILIKE %s
        ORDER BY last_updated DESC NULLS LAST
        LIMIT %s
        """,
        (q, q, q, req.limit),
    )
    return {"tool": "search_db", "rows": rows}


@app.post("/get_project")
def get_project(req: ProjectRequest, _: bool = Depends(require_auth)):
    q = f"%{req.project_code_or_name}%"
    row = fetch_one(
        """
        SELECT *
        FROM projects
        WHERE project_code ILIKE %s OR project_name ILIKE %s
        ORDER BY last_updated DESC NULLS LAST
        LIMIT 1
        """,
        (q, q),
    )
    return {"tool": "get_project", "project": row}


@app.post("/get_action_items")
def get_action_items(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        SELECT ai.task_text, ai.status, ai.priority, ai.due_date, p.project_name
        FROM action_items ai
        LEFT JOIN projects p ON ai.project_id = p.id
        WHERE ai.task_text ILIKE %s OR p.project_name ILIKE %s
        ORDER BY ai.due_date ASC NULLS LAST
        LIMIT %s
        """,
        (q, q, req.limit),
    )
    return {"tool": "get_action_items", "rows": rows}


@app.post("/get_vendor")
def get_vendor(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        SELECT v.*, e.display_name
        FROM vendors v
        JOIN entities e ON v.entity_id = e.id
        WHERE e.display_name ILIKE %s OR v.vendor_category ILIKE %s OR v.service_area ILIKE %s
        ORDER BY v.quality_score DESC NULLS LAST
        LIMIT %s
        """,
        (q, q, q, req.limit),
    )
    return {"tool": "get_vendor", "rows": rows}


@app.post("/get_ratecard")
def get_ratecard(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        SELECT e.display_name AS vendor, r.item_name, r.item_category, r.unit,
               r.internal_price, r.external_price, r.lead_time_days, r.valid_until, r.approval_status
        FROM ratecards r
        JOIN vendors v ON r.vendor_id = v.id
        JOIN entities e ON v.entity_id = e.id
        WHERE r.item_name ILIKE %s OR r.item_category ILIKE %s OR e.display_name ILIKE %s
        ORDER BY r.internal_price ASC NULLS LAST
        LIMIT %s
        """,
        (q, q, q, req.limit),
    )
    return {"tool": "get_ratecard", "rows": rows}


@app.post("/search_wiki")
def search_wiki(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        SELECT slug, title, category, summary, last_reviewed_at, version
        FROM wiki_pages
        WHERE approval_status = 'approved'
          AND (title ILIKE %s OR summary ILIKE %s OR content ILIKE %s)
        ORDER BY updated_at DESC NULLS LAST
        LIMIT %s
        """,
        (q, q, q, req.limit),
    )
    return {"tool": "search_wiki", "rows": rows}


@app.post("/generate_report")
def generate_report(req: SearchRequest, _: bool = Depends(require_auth)):
    # MVP: return structured source data; Donna/report skill writes narrative.
    projects = fetch_all(
        """
        SELECT project_code, project_name, status, risk_level, gross_margin_percent, latest_summary
        FROM projects
        ORDER BY risk_level DESC NULLS LAST, last_updated DESC NULLS LAST
        LIMIT 50
        """
    )
    actions = fetch_all(
        """
        SELECT task_text, status, priority, due_date
        FROM action_items
        WHERE status != 'done'
        ORDER BY due_date ASC NULLS LAST
        LIMIT 50
        """
    )
    return {"tool": "generate_report", "report_type": req.query, "projects": projects, "actions": actions}
```

---

# 27. First 10 Production Skill Specs

These are written as skill briefs that can be converted into Hermes/OpenClaw skill files.

---

## 27.1 `skills/query/query_router.md`

```markdown
# Skill: query_router

## Purpose
Classify a user query and choose the fastest safe retrieval path.

## Input
Raw user query, user_id, role, channel, optional project/client/vendor context.

## Output JSON
{
  "query_type": "structured_operational | wiki_truth | evidence_lookup | relationship_context | report_generation",
  "primary_tool": "search_db | search_wiki | search_evidence | get_project | get_vendor | get_ratecard | generate_report",
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

## Routing Rules
- Questions about status, budget, vendor, contact, project, task: structured_operational.
- Questions about SOP, policy, approved process: wiki_truth.
- Questions asking “what did they say,” “last discussion,” “from chat,” “from meeting”: evidence_lookup.
- Questions asking patterns, history, relationship, why recurring issue happens: relationship_context.
- Questions asking report, summary, weekly, monthly, variance, dashboard: report_generation.

## Constraints
Never retrieve more than 10 rows and 10 chunks unless the user explicitly asks for broad export.
Prefer SQL before semantic retrieval.
```

---

## 27.2 `skills/classify/classify_entry.md`

```markdown
# Skill: classify_entry

## Purpose
Classify raw input from WhatsApp, Telegram, Discord, ClickUp, web form, GDrive metadata, or API.

## Input
Raw text and metadata.

## Output JSON
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

## Rules
- Budget, ratecard, vendor price, margin, contract, and client negotiation are confidential by default.
- Legal/IP unreleased information is restricted by default.
- If project is not detected, ask user to confirm project.
- If confidence is below 0.85, mark needs_confirmation true.
```

---

## 27.3 `skills/extract/extract_ratecard.md`

```markdown
# Skill: extract_ratecard

## Purpose
Extract vendor pricing into structured ratecard JSON.

## Input
Raw text or document content.

## Output JSON
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

## Extraction Notes
- Convert Indonesian shorthand: 45jt = 45000000.
- If only one price is given, treat as internal_price unless user says selling/external.
- Guess item_category from item_name when possible.
- Do not approve automatically.
```

---

## 27.4 `skills/extract/extract_meeting_minutes.md`

```markdown
# Skill: extract_meeting_minutes

## Purpose
Convert raw MOM or transcript into structured meeting, decisions, and action items.

## Output JSON
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

## Rules
- Deadlines mentioned as “tomorrow,” “Friday,” etc. must be normalized to dates by Donna using current timezone WIB.
- If owner is unclear, set owner null and add to missing_fields.
```

---

## 27.5 `skills/extract/extract_budget.md`

```markdown
# Skill: extract_budget

## Purpose
Extract project budget and budget items from pasted text, spreadsheet text, PDF table, or chat.

## Output JSON
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

## Rules
- Calculate missing totals where possible.
- Flag any item with profit_percent below 20%.
- Do not overwrite approved budget without explicit approval.
```

---

## 27.6 `skills/db/upsert_ratecard.md`

```markdown
# Skill: upsert_ratecard

## Purpose
Write or update vendor and ratecard data into Postgres through MCP.

## Input
Structured JSON from extract_ratecard.

## Behavior
1. Find or create vendor entity.
2. Find or create vendor record.
3. Insert ratecard as pending_review.
4. Link project if present.
5. Write audit log.
6. Return saved record ID and summary.

## Output
{
  "status": "saved | needs_confirmation | failed",
  "vendor_id": null,
  "ratecard_id": null,
  "summary": null,
  "next_action": null
}
```

---

## 27.7 `skills/db/upsert_meeting.md`

```markdown
# Skill: upsert_meeting

## Purpose
Write meeting, decisions, and action items into Postgres.

## Behavior
1. Match project/client/business unit.
2. Insert meeting record.
3. Insert decisions.
4. Insert action items.
5. Update project latest_summary if relevant.
6. Create wiki draft suggestion if meeting is strategic.
7. Return confirmation.
```

---

## 27.8 `skills/wiki/generate_wiki_draft.md`

```markdown
# Skill: generate_wiki_draft

## Purpose
Generate human-readable wiki draft from structured database records and evidence.

## Inputs
Entity type, entity ID, source records, evidence chunks.

## Rules
- Never publish directly.
- Always set approval_status: draft.
- Include source documents.
- Include last_reviewed and freshness_rule.

## Output
Markdown page with YAML frontmatter.
```

---

## 27.9 `skills/reports/weekly_project_report.md`

```markdown
# Skill: weekly_project_report

## Purpose
Generate weekly management report grouped by BU.

## Data Sources
- projects
- project_updates
- budgets
- action_items
- meetings
- decisions
- GBrain context

## Output Format
1. Executive Summary
2. Projects On Track
3. Projects At Risk
4. Budget / Margin Issues
5. Open Decisions
6. Open Action Items
7. Required Chandra Attention
8. Next Week Priorities

## Rules
- Use SQL first.
- Include source references.
- Keep concise.
```

---

## 27.10 `skills/query/hybrid_answer.md`

```markdown
# Skill: hybrid_answer

## Purpose
Synthesize retrieved SQL rows, wiki pages, evidence chunks, and GBrain relationships into a concise answer.

## Rules
- Do not invent facts.
- If source is missing, say source unavailable.
- Always include last updated when available.
- Include confidence level.
- For confidential info, check permission before answering.
```

---

# 28. Dashboard Specifications

## 28.1 Founder Dashboard

### Widgets

1. Group revenue by BU
2. Gross margin by BU
3. Projects at risk
4. Budget variance over 5%
5. AR / collection risk
6. Open high-priority action items
7. Vendor issues
8. Client follow-up gaps
9. Weekly decisions
10. Cross-BU opportunities

### Filters

- Business unit
- Director
- Project status
- Date range
- Client
- Risk level

### Example SQL

```sql
SELECT bu.name, SUM(p.revenue) AS revenue, AVG(p.gross_margin_percent) AS avg_margin
FROM projects p
JOIN business_units bu ON p.business_unit_id = bu.id
GROUP BY bu.name
ORDER BY revenue DESC;
```

```sql
SELECT project_code, project_name, risk_level, latest_summary, last_updated
FROM projects
WHERE risk_level IN ('high', 'critical')
ORDER BY last_updated DESC;
```

---

## 28.2 Director Dashboard

### Finance Director

- Budget vs actual
- Margin compliance
- Projects below margin guardrail
- AR risk
- Payment approval queue

### Operations Director

- Vendor SLA
- Procurement lead time
- OTOB projects
- Production blockers
- Logistics risks

### Commerce Director

- Pipeline
- Proposal status
- New clients
- Cross-sell revenue
- Client retention

### Creative Director

- Creative backlog
- Design approval rate
- Revision rate
- Time to market
- IP/format innovation

---

## 28.3 Manager Dashboard

### Widgets

- My active projects
- My open action items
- Project status updates
- Latest MOMs
- Budget summary
- Vendor contacts
- Drive links
- Pending approvals

### Example SQL

```sql
SELECT project_code, project_name, status, risk_level, latest_summary
FROM projects
WHERE project_manager_id = :current_user_id
ORDER BY last_updated DESC;
```

```sql
SELECT task_text, due_date, priority, status
FROM action_items
WHERE owner_id = :current_user_id
AND status != 'done'
ORDER BY due_date ASC;
```

---

# 29. Connection Guide for Other Agent VPSes

## 29.1 Rule

Other VPSes must not connect directly to Postgres.

They connect only through MCP:

```text
Agent VPS → MCP API → permission check → Postgres/Wiki/GBrain → response
```

## 29.2 Agent Config Example

```yaml
provaliant_brain:
  type: mcp
  endpoint: "http://BRAIN_VPS_IP:8000"
  api_key: "CHANGE_ME_SECRET_API_KEY"
  default_user_role: "agent"
  timeout_seconds: 30
  tools:
    - search_db
    - search_wiki
    - search_evidence
    - get_project
    - get_vendor
    - get_ratecard
    - get_action_items
    - generate_report
```

## 29.3 Test Connection

```bash
curl -H "Authorization: Bearer CHANGE_ME_SECRET_API_KEY" \
  http://BRAIN_VPS_IP:8000/health
```

Expected:

```json
{
  "status": "ok",
  "service": "provaliant-brain-os"
}
```

---

# 30. User Guide for Managers

## 30.1 Basic Commands

```text
/status CPP
/budget CPP
/tasks me
/mom SNP
/vendor compare booth
/wiki procurement SOP
/report weekly
```

## 30.2 Entry Commands

```text
/entry project_update
/entry meeting
/entry vendor_quote
/entry budget
/entry contact
/entry proposal
/entry design_link
/entry issue
/entry decision
```

## 30.3 Example: Project Update

```text
/entry project_update
Project: CPP
Status: At risk
Issue: Vendor delivery delayed 2 days
Next step: Hueny to confirm new delivery date tomorrow
```

Donna should reply:

```text
Detected project update:
Project: CPP
Status: At risk
Issue: Vendor delivery delayed 2 days
Owner: Hueny
Next step: Confirm new delivery date

Saved as project update. Risk level changed to High.
```

## 30.4 Example: Vendor Quote

```text
/entry vendor_quote
Vendor: ABC Production
Item: Booth Production
Price: 45jt
Lead time: 10 days
Project: CPP
```

Donna should reply:

```text
Detected vendor quote:
Vendor: ABC Production
Item: Booth Production
Internal Price: Rp45,000,000
Lead Time: 10 days
Project: CPP
Status: Pending approval

Saved to ratecards.
```

---

# 31. Rollout Plan

## Week 1 — Technical Foundation

- Provision Brain VPS
- Install Postgres + pgvector
- Deploy schema
- Deploy MCP skeleton
- Seed users, roles, business units
- Test remote agent connection

## Week 2 — First Workflows

- Build first 10 skills
- Test WhatsApp/Telegram manual entry
- Test ratecard ingestion
- Test MOM extraction
- Test budget extraction
- Test query router

## Week 3 — Wiki and Drive

- Create wiki structure
- Create templates
- Sync first Drive folders
- Generate first wiki drafts
- Approve first project/client/vendor pages

## Week 4 — Reports and Manager Pilot

- Launch manager pilot with 3–5 users
- Generate weekly project report
- Generate budget variance report
- Generate action item report
- Fix extraction and permission issues

## Week 5 — Director Dashboards

- Build Founder dashboard
- Build Director dashboards
- Add KPI views
- Add report export

## Week 6 — Company Rollout

- Train managers and supervisors
- Enforce MOM/project update entry
- Weekly wiki review
- Weekly data quality review

---

# 32. Immediate Build Checklist

```text
[ ] Create repo
[ ] Add .env
[ ] Run install_brain_vps.sh
[ ] Run setup_db.sh
[ ] Deploy MCP server
[ ] Test /health
[ ] Test /search_db
[ ] Test /get_project
[ ] Add first skills
[ ] Add first wiki templates
[ ] Seed business units
[ ] Seed key projects
[ ] Seed first vendors
[ ] Connect Donna/OpenClaw to MCP
[ ] Test WhatsApp entry
[ ] Test Telegram query
[ ] Generate first weekly report
```

---

# 33. Next Prompt to Continue Build

Use this prompt next:

```text
Based on the Provaliant Brain OS PRD and Build Pack, generate the complete db/schema.sql, db/indexes.sql, db/rls.sql, and seed files for roles and business units. Make it production-ready for Postgres + pgvector and optimized for project, budget, vendor, meeting, action item, wiki, and evidence search.
```

