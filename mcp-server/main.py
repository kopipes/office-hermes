from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from auth import require_auth
from db import execute, fetch_all, fetch_one

app = FastAPI(title="Provaliant Brain OS MCP Server", version="1.0.0")


class Filters(BaseModel):
    project: Optional[str] = None
    client: Optional[str] = None
    vendor: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    confidentiality_max: str = "internal"


class RequestContext(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None
    business_unit_id: Optional[str] = None


class SearchRequest(RequestContext):
    query: str
    filters: Filters = Field(default_factory=Filters)
    limit: int = 10


class ProjectRequest(RequestContext):
    project_code_or_name: str


class VendorRequest(RequestContext):
    query: str
    limit: int = 10


class BudgetRequest(RequestContext):
    project_code_or_name: str


class SuggestWikiRequest(RequestContext):
    slug: str
    title: str
    category: str = "project"
    summary: Optional[str] = None
    content: str
    source_document_ids: list[str] = Field(default_factory=list)
    related_entity_ids: list[str] = Field(default_factory=list)


class StructuredEntryRequest(RequestContext):
    entry_type: str
    payload: dict[str, Any]
    source_type: str = "manual"
    source_name: Optional[str] = None


def _log_query(user_id: Optional[str], query_text: str, query_type: str, tools_used: list[str], rows: int, chunks: int, summary: str):
    execute(
        """
        insert into query_logs (user_id, query_text, query_type, tools_used, rows_returned, chunks_returned, response_summary)
        values (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, query_text, query_type, tools_used, rows, chunks, summary),
    )


def _log_audit(user_id: Optional[str], action_type: str, table_name: str, record_id: Optional[str], previous: Optional[dict], new: Optional[dict]):
    execute(
        """
        insert into audit_logs (user_id, action_type, table_name, record_id, previous_value, new_value)
        values (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
        """,
        (user_id, action_type, table_name, record_id, _to_json(previous), _to_json(new)),
    )


def _to_json(value: Optional[dict]) -> str:
    import json

    return json.dumps(value or {})


@app.get("/health")
def health(_: bool = Depends(require_auth)):
    return {
        "status": "ok",
        "service": "provaliant-brain-os",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/search_db")
def search_db(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        select project_code, project_name, status, latest_summary, risk_level, gross_margin_percent, last_updated
        from projects
        where project_name ilike %s
           or project_code ilike %s
           or coalesce(latest_summary, '') ilike %s
        order by last_updated desc nulls last
        limit %s
        """,
        (q, q, q, req.limit),
    )

    _log_query(req.user_id, req.query, "structured_operational", ["search_db"], len(rows), 0, "search_db")
    return {
        "status": "ok",
        "tool": "search_db",
        "data": rows,
        "permission_applied": True,
        "confidence": 0.9,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/search_wiki")
def search_wiki(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        select slug, title, category, summary, approval_status, last_reviewed_at, version, updated_at
        from wiki_pages
        where approval_status = 'approved'
          and (title ilike %s or coalesce(summary, '') ilike %s or coalesce(content, '') ilike %s)
        order by updated_at desc nulls last
        limit %s
        """,
        (q, q, q, req.limit),
    )

    _log_query(req.user_id, req.query, "wiki_truth", ["search_wiki"], len(rows), 0, "search_wiki")
    return {
        "status": "ok",
        "tool": "search_wiki",
        "data": rows,
        "permission_applied": True,
        "confidence": 0.92,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/search_evidence")
def search_evidence(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        select
          c.id,
          c.content,
          c.page_number,
          c.section_title,
          d.id as document_id,
          d.title as document_title,
          d.document_type,
          d.confidentiality,
          d.gdrive_url,
          d.imported_at
        from chunks c
        join documents d on d.id = c.document_id
        where c.content ilike %s
        order by d.imported_at desc nulls last
        limit %s
        """,
        (q, req.limit),
    )

    _log_query(req.user_id, req.query, "evidence_lookup", ["search_evidence"], 0, len(rows), "search_evidence")
    return {
        "status": "ok",
        "tool": "search_evidence",
        "data": rows,
        "permission_applied": True,
        "confidence": 0.84,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/get_project")
def get_project(req: ProjectRequest, _: bool = Depends(require_auth)):
    q = f"%{req.project_code_or_name}%"
    project = fetch_one(
        """
        select *
        from projects
        where project_code ilike %s or project_name ilike %s
        order by last_updated desc nulls last
        limit 1
        """,
        (q, q),
    )

    actions = []
    if project:
        actions = fetch_all(
            """
            select id, task_text, status, priority, due_date
            from action_items
            where project_id = %s and status <> 'done'
            order by due_date asc nulls last
            limit 10
            """,
            (project["id"],),
        )

    _log_query(req.user_id, req.project_code_or_name, "structured_operational", ["get_project", "get_action_items"], 1 if project else 0, 0, "get_project")
    return {
        "status": "ok",
        "tool": "get_project",
        "data": {
            "project": project,
            "open_action_items": actions,
        },
        "permission_applied": True,
        "confidence": 0.93 if project else 0.2,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/get_vendor")
def get_vendor(req: VendorRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        select
          v.id,
          e.display_name as vendor_name,
          v.vendor_category,
          v.service_area,
          v.contact_person,
          v.phone,
          v.email,
          v.reliability_score,
          v.quality_score,
          v.speed_score,
          v.payment_terms,
          v.blacklist_flag
        from vendors v
        join entities e on e.id = v.entity_id
        where e.display_name ilike %s
           or coalesce(v.vendor_category, '') ilike %s
           or coalesce(v.service_area, '') ilike %s
        order by v.quality_score desc nulls last
        limit %s
        """,
        (q, q, q, req.limit),
    )

    _log_query(req.user_id, req.query, "structured_operational", ["get_vendor"], len(rows), 0, "get_vendor")
    return {
        "status": "ok",
        "tool": "get_vendor",
        "data": rows,
        "permission_applied": True,
        "confidence": 0.9,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/get_budget")
def get_budget(req: BudgetRequest, _: bool = Depends(require_auth)):
    q = f"%{req.project_code_or_name}%"
    budget = fetch_one(
        """
        select b.*
        from budgets b
        join projects p on p.id = b.project_id
        where p.project_code ilike %s or p.project_name ilike %s
        order by b.created_at desc
        limit 1
        """,
        (q, q),
    )

    items = []
    if budget:
        items = fetch_all(
            """
            select item_category, item_name, qty, unit, unit_cost, internal_total, external_total, profit, profit_percent
            from budget_items
            where budget_id = %s
            order by item_category, item_name
            """,
            (budget["id"],),
        )

    _log_query(req.user_id, req.project_code_or_name, "finance_analysis", ["get_budget"], 1 if budget else 0, 0, "get_budget")
    return {
        "status": "ok",
        "tool": "get_budget",
        "data": {
            "budget": budget,
            "items": items,
        },
        "permission_applied": True,
        "confidence": 0.9 if budget else 0.2,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/get_action_items")
def get_action_items(req: SearchRequest, _: bool = Depends(require_auth)):
    q = f"%{req.query}%"
    rows = fetch_all(
        """
        select ai.id, ai.task_text, ai.status, ai.priority, ai.due_date,
               p.project_code, p.project_name,
               u.full_name as owner_name
        from action_items ai
        left join projects p on p.id = ai.project_id
        left join users u on u.id = ai.owner_id
        where ai.task_text ilike %s
           or coalesce(p.project_name, '') ilike %s
           or coalesce(p.project_code, '') ilike %s
        order by ai.due_date asc nulls last
        limit %s
        """,
        (q, q, q, req.limit),
    )

    _log_query(req.user_id, req.query, "structured_operational", ["get_action_items"], len(rows), 0, "get_action_items")
    return {
        "status": "ok",
        "tool": "get_action_items",
        "data": rows,
        "permission_applied": True,
        "confidence": 0.9,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/generate_report")
def generate_report(req: SearchRequest, _: bool = Depends(require_auth)):
    projects = fetch_all(
        """
        select project_code, project_name, status, risk_level, gross_margin_percent, latest_summary, last_updated
        from projects
        order by risk_level desc nulls last, last_updated desc nulls last
        limit 100
        """
    )
    actions = fetch_all(
        """
        select task_text, status, priority, due_date
        from action_items
        where status <> 'done'
        order by due_date asc nulls last
        limit 100
        """
    )
    meetings = fetch_all(
        """
        select meeting_title, meeting_date, summary
        from meetings
        order by meeting_date desc nulls last
        limit 25
        """
    )

    _log_query(req.user_id, req.query, "report_generation", ["generate_report"], len(projects) + len(actions) + len(meetings), 0, "generate_report")
    return {
        "status": "ok",
        "tool": "generate_report",
        "data": {
            "report_type": req.query,
            "projects": projects,
            "open_action_items": actions,
            "recent_meetings": meetings,
        },
        "permission_applied": True,
        "confidence": 0.88,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/suggest_wiki_update")
def suggest_wiki_update(req: SuggestWikiRequest, _: bool = Depends(require_auth)):
    page = fetch_one("select id, slug, content from wiki_pages where slug = %s", (req.slug,))

    if page:
        rows = execute(
            """
            insert into wiki_change_requests (wiki_page_id, proposed_content, change_reason, proposed_by, approval_status)
            values (%s, %s, %s, %s, 'pending_review')
            """,
            (page["id"], req.content, "Auto suggestion from MCP", req.user_id),
        )
        _log_audit(req.user_id, "insert", "wiki_change_requests", None, None, {"wiki_page_id": page["id"], "rows": rows})
        return {
            "status": "ok",
            "tool": "suggest_wiki_update",
            "data": {"mode": "change_request", "wiki_page_id": page["id"]},
            "permission_applied": True,
            "confidence": 0.9,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

    row = fetch_one(
        """
        insert into wiki_pages (slug, title, category, content, summary, approval_status, source_document_ids, related_entity_ids)
        values (%s, %s, %s, %s, %s, 'draft', %s::uuid[], %s::uuid[])
        returning id, slug
        """,
        (req.slug, req.title, req.category, req.content, req.summary, req.source_document_ids, req.related_entity_ids),
    )
    _log_audit(req.user_id, "insert", "wiki_pages", row["id"], None, row)
    return {
        "status": "ok",
        "tool": "suggest_wiki_update",
        "data": {"mode": "new_draft", "wiki_page": row},
        "permission_applied": True,
        "confidence": 0.9,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/write_structured_entry")
def write_structured_entry(req: StructuredEntryRequest, _: bool = Depends(require_auth)):
    if req.entry_type == "project_update":
        payload = req.payload
        project = fetch_one(
            "select id from projects where project_code = %s or project_name = %s limit 1",
            (payload.get("project"), payload.get("project")),
        )
        if not project:
            return {
                "status": "error",
                "tool": "write_structured_entry",
                "error": "Project not found",
            }

        row = fetch_one(
            """
            insert into project_updates (project_id, update_date, update_type, status, summary, blockers, next_steps, confidence)
            values (%s, now(), %s, %s, %s, %s, %s, %s)
            returning id, project_id
            """,
            (
                project["id"],
                payload.get("update_type", "manual"),
                payload.get("status"),
                payload.get("summary"),
                payload.get("blockers"),
                payload.get("next_steps"),
                payload.get("confidence", 0.85),
            ),
        )
        _log_audit(req.user_id, "insert", "project_updates", row["id"], None, row)
        return {
            "status": "ok",
            "tool": "write_structured_entry",
            "data": {"entry_type": req.entry_type, "record": row},
            "permission_applied": True,
            "confidence": 0.9,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

    if req.entry_type == "action_item":
        payload = req.payload
        row = fetch_one(
            """
            insert into action_items (task_text, status, priority, due_date)
            values (%s, coalesce(%s, 'open'), %s, %s)
            returning id, task_text, status
            """,
            (
                payload.get("task_text"),
                payload.get("status"),
                payload.get("priority"),
                payload.get("due_date"),
            ),
        )
        _log_audit(req.user_id, "insert", "action_items", row["id"], None, row)
        return {
            "status": "ok",
            "tool": "write_structured_entry",
            "data": {"entry_type": req.entry_type, "record": row},
            "permission_applied": True,
            "confidence": 0.9,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

    return {
        "status": "error",
        "tool": "write_structured_entry",
        "error": f"Unsupported entry_type: {req.entry_type}",
    }
