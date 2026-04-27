# Provaliant Brain OS - Enterprise System Blueprint

**Version:** 3.0  
**Owner:** Chandra Sugiono / Provaliant Group  
**Target Platform:** Dedicated Second Brain VPS + Hermes Agent / OpenClaw agent VPSes  
**Primary Interfaces:** WhatsApp, Telegram, Discord, ClickUp, Web Wiki, Dashboards  
**Core Principle:** Database first. Wiki approved. GBrain enhanced. Skills orchestrated. MCP controlled.

---

## 1. Executive Blueprint

Provaliant Brain OS is a dedicated company knowledge and operations platform. It is not a generic chatbot and not a document dump. It is a multi-user operational brain where:

- Postgres stores structured truth.
- pgvector stores searchable evidence.
- GBrain stores relationships and context.
- Markdown Wiki stores approved human-readable knowledge.
- Hermes/OpenClaw Skills replace external workflow automation.
- MCP/API is the only controlled gateway for other agents and VPSes.
- Donna routes, retrieves, summarizes, reports, and asks for confirmation.

The system is designed so an LLM never reads the whole company archive. Instead, the database and search layer retrieve only the small set of records needed for an answer.

### North Star

```text
Managers stop asking people where information is.
Managers ask Donna, and Donna retrieves trusted operational knowledge fast.
```

---

## 2. Target Outcomes

| Outcome | Description | Success Metric |
|---|---|---|
| Fast knowledge retrieval | Managers can find project, budget, vendor, MOM, SOP, and contact data quickly. | Common queries under 3 seconds before LLM synthesis |
| Structured operational memory | Chat, Drive, PM API, and manual entries become database records. | 80 percent of recurring knowledge captured in structured tables |
| Trusted wiki | Only approved summaries and SOPs become official wiki knowledge. | Wiki pages have owner, status, source, and review date |
| Multi-user entry | Managers, supervisors, and staff can submit updates from normal channels. | At least 5 pilot users entering data weekly |
| Report automation | Weekly project, budget, task, vendor, and KPI reports generated from data. | Reports produced in less than 60 seconds |
| Governance | Every query and write is permission-controlled and logged. | 100 percent of writes have audit trail |

---

## 3. Architecture Overview

### 3.1 Deployment Topology

```text
                 +-----------------------------------+
                 | Agent VPSes                       |
                 | Donna / Manager Agents / BU Bots  |
                 +------------------+----------------+
                                    |
                                    | Secure MCP/API calls only
                                    v
+-----------------------------------------------------------------------+
| Dedicated Second Brain VPS                                            |
|                                                                       |
|  +------------------+    +------------------+    +------------------+ |
|  | MCP/API Server   | -> | Permission Layer | -> | Query Router     | |
|  +------------------+    +------------------+    +------------------+ |
|              |                         |                         |    |
|              v                         v                         v    |
|  +------------------+    +------------------+    +------------------+ |
|  | Postgres         |    | pgvector Chunks  |    | GBrain Graph     | |
|  | Structured Truth |    | Evidence Search  |    | Relationships    | |
|  +------------------+    +------------------+    +------------------+ |
|              |                                                    |    |
|              v                                                    v    |
|  +------------------+                              +----------------+ |
|  | Markdown Wiki    |                              | Audit Logs     | |
|  | Approved Truth   |                              | Query Logs     | |
|  +------------------+                              +----------------+ |
+-----------------------------------------------------------------------+
```

### 3.2 System Rule

Other VPSes must not connect directly to Postgres, raw files, or wiki storage. They must use authenticated MCP/API tools only.

```text
Agent VPS -> MCP/API -> Permission check -> Database/Wiki/GBrain -> Filtered response
```

---

## 4. Component Responsibilities

| Component | Responsibility | Must Not Do |
|---|---|---|
| Postgres | Structured source of truth for projects, clients, vendors, budgets, tasks, meetings, KPIs | Store unstructured chaos without metadata |
| pgvector | Semantic retrieval over chunks and wiki pages | Replace structured SQL filtering |
| GBrain | Relationship layer and context enrichment | Become the primary database |
| Markdown Wiki | Approved human-readable knowledge | Automatically trust raw chat data |
| MCP/API Server | Controlled gateway for agents and tools | Expose database publicly |
| Hermes Skills | Workflow engine for intake, extraction, validation, reporting | Depend on n8n or external workflow tools |
| Donna | Orchestration, query routing, synthesis, confirmation, reports | Hallucinate without sources |

---

## 5. Data Sources

| Source | Ingestion Method | Destination |
|---|---|---|
| WhatsApp personal and groups | Intake skill and parser | sources, documents, chunks, structured records |
| Telegram personal and groups | Intake skill and parser | sources, documents, chunks, structured records |
| Discord / ClickUp | Command or API intake | project updates, tasks, comments |
| Google Drive | Folder watcher and metadata sync | documents, chunks, drive_links, wiki drafts |
| PM Provaliant API | Scheduled API sync | projects, tasks, budgets, status updates |
| Website | Controlled public crawler or manual import | public wiki, company profile, case studies |
| Manual web form | Structured entry form | direct structured records |

---

## 6. Data Model Blueprint

### 6.1 Core Domains

```text
Identity and Access
- users
- roles
- permissions
- business_units

Knowledge Sources
- sources
- documents
- chunks
- drive_links
- citations

Business Entities
- entities
- clients
- contacts
- vendors
- IPs
- malls
- brands

Operations
- projects
- project_updates
- meetings
- decisions
- action_items
- issues

Finance and Purchasing
- budgets
- budget_items
- ratecards
- vendor_scorecards
- purchase_requests

Knowledge Layer
- wiki_pages
- wiki_change_requests
- wiki_page_entities

Reporting and Governance
- reports
- query_logs
- audit_logs
- ingestion_jobs
```

### 6.2 Entity Relationship Summary

```text
Client -> Projects
Project -> Budgets
Project -> Meetings
Project -> Action Items
Project -> Documents
Project -> Vendors
Vendor -> Ratecards
Budget -> Budget Items
Meeting -> Decisions
Meeting -> Action Items
Wiki Page -> Source Documents
Entity -> Wiki Pages
Entity -> GBrain Relationships
```

---

## 7. Database Tables - Production Blueprint

### 7.1 Identity and Access

| Table | Purpose |
|---|---|
| users | People and agent accounts that access the system |
| roles | Founder, Director, BU Head, Manager, Supervisor, Staff, Agent |
| business_units | Premium, Sports, Retail, Starlight, Futurevast, Event, Studios, etc. |
| role_permissions | Permission matrix by role, table, action, and classification |

### 7.2 Knowledge Source Tables

| Table | Purpose |
|---|---|
| sources | Origin of every input: WhatsApp, Telegram, Drive, API, manual |
| documents | File or message level record with metadata, owner, status, confidentiality |
| chunks | Searchable text chunks with embeddings and page/section metadata |
| drive_links | Google Drive folder and file links connected to projects, clients, and designs |
| citations | Evidence trail linking answers/wiki pages to source chunks |

### 7.3 Business Tables

| Table | Purpose |
|---|---|
| entities | Master registry for clients, vendors, persons, projects, brands, IPs |
| clients | Client profile, type, tier, account owner, follow-up status |
| contacts | People at clients, vendors, malls, licensors, partners |
| vendors | Vendor profile, category, scoring, terms, blacklist flag |
| ratecards | Vendor rates by item, unit, price, validity, approval status |
| projects | Project master data from PM Provaliant and manual updates |
| project_updates | Time-series project status and risk updates |
| budgets | Budget header per project and version |
| budget_items | Budget line items, internal price, external price, margin |
| meetings | Meeting metadata and summary |
| decisions | Decisions made, owner, impact, evidence |
| action_items | Tasks from meetings, chats, and project management |

### 7.4 Knowledge and Governance Tables

| Table | Purpose |
|---|---|
| wiki_pages | Approved or draft Markdown wiki content in searchable database form |
| wiki_change_requests | Proposed changes from new evidence, pending review |
| reports | Generated reports and their source references |
| query_logs | Every query made through MCP/API |
| audit_logs | Every write/update/delete action |
| ingestion_jobs | Status of document/chat/API ingestion jobs |

---

## 8. Query Architecture

### 8.1 Retrieval Priority

```text
1. SQL for structured facts
2. Wiki for approved truth
3. GBrain for relationships and context
4. pgvector for evidence chunks
5. LLM for final synthesis only
```

### 8.2 Query Types

| Query Type | Example | Route |
|---|---|---|
| structured_operational | What is CPP status? | SQL -> summary |
| finance_analysis | Which projects are under 20 percent margin? | SQL -> calculations -> answer |
| wiki_truth | What is procurement SOP? | Approved wiki only |
| evidence_lookup | What did client say last meeting? | chunks + documents + citations |
| relationship_context | What history do we have with this vendor? | GBrain + SQL + evidence |
| report_generation | Generate weekly management report | SQL + wiki + GBrain + LLM synthesis |

### 8.3 Context Budget Rule

For normal answers:

```text
Max SQL rows: 10
Max wiki pages: 5
Max chunks: 10
Max GBrain relationships: 20
```

For reports:

```text
Max SQL rows: 100
Max wiki pages: 10
Max chunks: 25
Max GBrain relationships: 50
```

---

## 9. MCP/API Tool Contract

### 9.1 Required Tools

| Tool | Purpose |
|---|---|
| search_db | Search structured records by type, entity, BU, date, status |
| search_wiki | Search approved wiki pages |
| search_evidence | Search raw chunks and source documents |
| get_entity | Retrieve entity profile and relationships |
| get_project | Retrieve project status, budget, tasks, MOMs, links |
| get_vendor | Retrieve vendor profile and ratecards |
| get_budget | Retrieve project budget and budget items |
| get_action_items | Retrieve tasks by owner, project, BU, status |
| generate_report | Return report source data for skill-based synthesis |
| suggest_wiki_update | Create wiki draft or change request |
| write_structured_entry | Save validated structured data |

### 9.2 Standard Request Fields

```json
{
  "user_id": "uuid",
  "role": "manager",
  "business_unit_id": "uuid",
  "query": "status CPP",
  "filters": {
    "project": "CPP",
    "client": null,
    "vendor": null,
    "date_from": null,
    "date_to": null,
    "confidentiality_max": "internal"
  },
  "limit": 10
}
```

### 9.3 Standard Response Fields

```json
{
  "status": "ok",
  "tool": "get_project",
  "data": [],
  "sources": [],
  "permission_applied": true,
  "confidence": 0.92,
  "last_updated": "2026-04-27T10:00:00+07:00"
}
```

---

## 10. Skills Workflow Blueprint

### 10.1 Skill Categories

```text
intake/
- whatsapp_intake
- telegram_intake
- discord_intake
- clickup_intake
- gdrive_sync
- pm_provaliant_api_sync

classify/
- classify_entry
- detect_entity
- detect_confidentiality
- detect_business_unit

extract/
- extract_project_status
- extract_meeting_minutes
- extract_budget
- extract_ratecard
- extract_client_profile
- extract_vendor_profile
- extract_drive_links

db/
- upsert_project
- upsert_client
- upsert_vendor
- upsert_budget
- upsert_ratecard
- upsert_meeting
- upsert_decision
- upsert_action_item

wiki/
- generate_wiki_draft
- submit_wiki_for_approval
- publish_approved_wiki
- update_project_wiki
- update_vendor_wiki

gbrain/
- gbrain_entity_link
- gbrain_relationship_update
- gbrain_context_lookup
- gbrain_pattern_discovery

query/
- query_router
- sql_query
- wiki_search
- evidence_search
- hybrid_answer

reports/
- daily_manager_brief
- weekly_project_report
- budget_variance_report
- vendor_comparison_report
- project_health_report
- kpi_report
```

### 10.2 Generic Entry Workflow

```text
Input received
-> classify_entry
-> detect_entity
-> detect_confidentiality
-> select extraction skill
-> validate required fields
-> ask confirmation if confidence < 0.85
-> write to Postgres
-> update GBrain relationships
-> create wiki draft if important
-> notify user
-> write audit log
```

---

## 11. Workflow Examples

### 11.1 Vendor Quote

User:

```text
/entry vendor_quote
Vendor ABC quote booth 45jt, lead time 10 days, for CPP.
```

Flow:

```text
whatsapp_intake
-> classify_entry: vendor_quote
-> extract_ratecard
-> upsert_vendor
-> upsert_ratecard as pending_review
-> gbrain_relationship_update: Vendor ABC -> CPP
-> Donna confirms
```

### 11.2 Meeting MOM

User:

```text
/entry meeting
Project: SNP
Decision: launch moved to July 10
Action: Hueny confirm vendor by Friday
```

Flow:

```text
telegram_intake
-> classify_entry: meeting
-> extract_meeting_minutes
-> upsert_meeting
-> upsert_decision
-> upsert_action_item
-> update_project_latest_summary
-> suggest_wiki_update
```

### 11.3 Weekly Report

User:

```text
/report weekly
```

Flow:

```text
query_router: report_generation
-> generate_report tool retrieves project, budget, task, meeting data
-> gbrain_context_lookup finds recurring risks
-> weekly_project_report skill writes final report
-> output to WhatsApp/Telegram/Web
```

---

## 12. Security Blueprint

### 12.1 Classification Levels

| Level | Examples | Access |
|---|---|---|
| Public | Public website, published case studies | All users |
| Internal | SOPs, project summaries, general reports | Team users |
| Confidential | Budgets, margins, ratecards, contracts, negotiations | Managers and above by permission |
| Restricted | Legal disputes, unreleased IP, sensitive licensing | Chandra/approved directors only |

### 12.2 Controls

- MCP/API key required for all agent calls.
- User ID and role must be passed with every request.
- Postgres is not exposed publicly.
- Row-level security or application-level permission filtering.
- Every query logged.
- Every write audited.
- Wiki publish requires approval.
- Destructive actions require explicit human confirmation.

---

## 13. Dedicated Brain VPS Setup

### 13.1 Recommended VPS

| Component | Recommendation |
|---|---|
| OS | Ubuntu 22.04 LTS or newer |
| CPU | 4 to 8 vCPU |
| RAM | 16 GB recommended for production |
| Storage | 200 GB SSD minimum, expandable |
| Network | Private firewall, only MCP/API exposed |
| Backups | Daily database dump and wiki Git backup |

### 13.2 Services on Brain VPS

```text
Postgres + pgvector
MCP/API Server
Wiki repository
GBrain service or sync bridge
Ingestion workers
Embedding workers
Backup scripts
Health checks
Audit logs
```

### 13.3 Services NOT on Brain VPS

```text
General agent experimentation
Untrusted scripts
Public database access
Random file uploads without ingestion pipeline
```

---

## 14. Agent VPS Connection Model

### 14.1 Agent Types

| Agent VPS | Role |
|---|---|
| Donna Founder Agent | CEO-level orchestration and strategic queries |
| Manager Agent | BU manager access, project/task/report queries |
| Finance Agent | Budget, AR, margin, payment data |
| Operations Agent | Vendors, procurement, production, logistics |
| Creative Agent | Briefs, designs, style guides, approvals |

### 14.2 Connection Rule

```text
Agents are clients.
Brain VPS is the source of truth.
MCP/API is the gate.
```

### 14.3 Agent Config Example

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

---

## 15. Wiki Blueprint

### 15.1 Wiki Folder Structure

```text
wiki/
|-- company/
|-- clients/
|   |-- malls/
|   |-- brands/
|   |-- ip-owners/
|   `-- corporate/
|-- projects/
|   |-- active/
|   |-- completed/
|   `-- archive/
|-- finance/
|-- vendors/
|-- meetings/
|-- sops/
|-- ip-library/
`-- reports/
```

### 15.2 Wiki Page Template

```yaml
slug: projects/cpp-2026
title: CPP 2026 Project Overview
category: project
owner: operations
approval_status: approved
related_entities:
  - CPP
  - Paw Patrol
source_documents:
  - gdrive://folder-or-file-id
tags:
  - retail
  - event
  - operations
freshness_rule: weekly_review
last_reviewed: 2026-04-27
version: 1
```

### 15.3 Wiki Rule

```text
Raw evidence can suggest wiki updates.
Only approved wiki pages become operational truth.
```

---

## 16. Dashboard Blueprint

### 16.1 Founder Dashboard

| Widget | Data Source |
|---|---|
| Revenue by BU | projects, budgets, finance API |
| Gross margin by BU | projects, budgets, budget_items |
| Projects at risk | projects, project_updates, issues |
| Budget variance | budgets, budget_items |
| Open action items | action_items |
| Vendor issues | vendors, vendor_scorecards, project_updates |
| Client follow-up gaps | clients, contacts, meetings |
| Weekly decisions | decisions |

### 16.2 Director Dashboard

| Director | Dashboard Focus |
|---|---|
| Finance | margin, AR, budget adherence, cashflow risks |
| Operations | vendor SLA, procurement lead time, OTOB, logistics |
| Commerce | pipeline, proposals, new clients, cross-sell |
| Creative | backlog, approval rate, revision rate, time to market |

### 16.3 Manager Dashboard

```text
My projects
My tasks
Latest MOMs
Budget summary
Vendor comparison
Client contacts
Pending approvals
Drive links
```

---

## 17. Implementation Roadmap

### Phase 1 - Foundation

- Provision Brain VPS.
- Install Postgres + pgvector.
- Deploy schema and indexes.
- Deploy MCP/API skeleton.
- Seed roles, users, BUs.
- Test Agent VPS connection.

### Phase 2 - Core Skills

- Build classify_entry.
- Build extract_project_status.
- Build extract_meeting_minutes.
- Build extract_ratecard.
- Build extract_budget.
- Build upsert skills.
- Build query_router.

### Phase 3 - Ingestion

- WhatsApp intake.
- Telegram intake.
- Google Drive sync.
- PM Provaliant API sync.
- Document chunking and embedding.

### Phase 4 - Wiki

- Create wiki templates.
- Generate first drafts.
- Review and approve first pages.
- Sync wiki pages into database.

### Phase 5 - Reports and Dashboards

- Weekly project report.
- Budget variance report.
- Vendor comparison report.
- Action item report.
- Founder and manager dashboards.

### Phase 6 - Governance and Rollout

- Permission review.
- Audit log review.
- Manager training.
- Weekly data quality review.
- Company-wide rollout.

---

## 18. Build Checklist

```text
[ ] Brain VPS provisioned
[ ] Firewall configured
[ ] Postgres installed
[ ] pgvector installed
[ ] Database schema deployed
[ ] Indexes deployed
[ ] Roles and users seeded
[ ] MCP/API server deployed
[ ] Health endpoint tested
[ ] Agent VPS connected
[ ] Query logs working
[ ] Audit logs working
[ ] First skills installed
[ ] First project records seeded
[ ] First vendor ratecards entered
[ ] First MOM extracted
[ ] First wiki drafts generated
[ ] First weekly report generated
[ ] Manager pilot completed
```

---

## 19. Acceptance Criteria

| Area | Criteria |
|---|---|
| Performance | Structured queries under 300ms, wiki under 2s, evidence under 3s before synthesis |
| Accuracy | Common structured extraction above 85 percent confidence |
| Governance | All writes audited, all queries logged, permissions enforced |
| Adoption | Managers can use WhatsApp/Telegram commands without technical support |
| Reporting | Weekly project health report generated in less than 60 seconds |
| Wiki | Approved pages have owner, source, review date, version |

---

## 20. Operating Rhythm

### Daily

- Managers submit project updates.
- Supervisors submit issues and MOMs.
- Donna sends daily task and risk summaries.

### Weekly

- Weekly project health report.
- Budget variance report.
- Vendor issue review.
- Wiki draft approval session.

### Monthly

- KPI report.
- Client follow-up review.
- Vendor scorecard review.
- Data quality audit.

---

## 21. Prompt Library for Future Build Support

### Generate SQL Schema

```text
Based on the Provaliant Brain OS System Blueprint, generate complete production-ready PostgreSQL schema, indexes, RLS policies, and seed files for roles and business units.
```

### Generate MCP Server

```text
Based on the Provaliant Brain OS System Blueprint, generate a Python FastAPI MCP server with tools for search_db, search_wiki, search_evidence, get_project, get_vendor, get_budget, get_action_items, generate_report, and write_structured_entry.
```

### Generate Hermes Skills

```text
Based on the Provaliant Brain OS System Blueprint, generate production-ready Hermes/OpenClaw skills for classify_entry, extract_meeting_minutes, extract_budget, extract_ratecard, upsert_project, upsert_meeting, query_router, and weekly_project_report.
```

### Generate Dashboard Spec

```text
Based on the Provaliant Brain OS System Blueprint, generate detailed dashboard wireframes and SQL queries for Founder, Finance Director, Operations Director, Commerce Director, Creative Director, and Manager dashboards.
```

### Generate Rollout SOP

```text
Based on the Provaliant Brain OS System Blueprint, write the SOP for managers and supervisors to use WhatsApp, Telegram, and Web Wiki for entries, queries, MOMs, vendor quotes, budgets, and reports.
```

---

## 22. Final Blueprint Statement

Provaliant Brain OS should be built as a dedicated knowledge infrastructure, not as a single chatbot. The Brain VPS owns the truth. Agent VPSes query it. Skills structure the work. Wiki approves the truth. GBrain connects the context. Donna turns it into action.

```text
Database filters.
Wiki confirms.
GBrain connects.
Donna explains.
Managers act.
```
