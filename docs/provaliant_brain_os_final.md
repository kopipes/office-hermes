
# Provaliant Brain OS

## Product Requirements Document & Implementation Guide

**Version:** 1.0  
**Owner:** Chandra Sugiono / Provaliant Group  

---

## Executive Summary

Provaliant Brain OS is a **multi-user operational knowledge system** combining:

- Structured Database (Postgres)
- Semantic Memory (pgvector)
- Relationship Graph (GBrain)
- Approved Wiki (Markdown)
- AI Orchestration (Donna via Hermes/OpenClaw)

**Goal:**  
Fast, structured, multi-user access to company knowledge without relying on LLM full-context reading.

---

## Architecture Overview

```
Users (WhatsApp / Telegram / Web)
        ↓
       Donna (AI Router)
        ↓
       MCP Server
        ↓
Postgres (Truth) + pgvector (Search)
        ↓
       GBrain (Relationships)
        ↓
       Wiki (Approved Knowledge)
```

---

## Core Principles

1. Database does filtering, LLM does thinking  
2. Wiki = Truth, Open Brain = Memory  
3. Structured entry first  
4. Skills replace external workflow tools  
5. Every answer must have source  

---

## System Components

### 1. Database Layer
- Projects
- Clients
- Vendors
- Budgets
- Meetings
- Action Items
- Ratecards

### 2. Wiki Layer
- SOPs
- Project summaries
- Vendor summaries
- Client summaries

### 3. GBrain Layer
- Relationships
- Context linking
- Pattern detection

### 4. Skills Layer
- Intake
- Classification
- Extraction
- Database write
- Query routing
- Reporting

---

## Installation Summary

### Setup VPS
```
Ubuntu 22.04
8–16GB RAM
```

### Install Postgres
```
sudo apt install postgresql
```

### Install pgvector
```
git clone https://github.com/pgvector/pgvector.git
make && sudo make install
```

### Run MCP Server
```
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## User Commands

### Entry
```
/entry project_update
/entry meeting
/entry vendor_quote
/entry budget
```

### Query
```
/status CPP
/vendor compare booth
/budget CPP
/report weekly
```

---

## Example Workflow

User:
```
Vendor ABC quote booth 45jt
```

System:
```
Extract → Structure → Save → Link → Confirm
```

---

## Dashboard Overview

### Founder
- Revenue
- Margin
- Risk Projects

### Director
- KPI tracking
- BU performance

### Manager
- Project status
- Tasks
- Budgets

---

## Rollout Plan

### Week 1
- Setup DB + MCP

### Week 2
- Build skills

### Week 3
- Wiki + Drive

### Week 4
- Reports

### Week 5
- Dashboards

### Week 6
- Company rollout

---

## Key Outcome

```
Managers stop asking people
Managers ask Donna
```

---
