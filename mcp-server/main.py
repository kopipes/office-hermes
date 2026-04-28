import hashlib
import re
import time
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

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


class BrainQueryRequest(RequestContext):
    query: str
    channel: Optional[str] = None
    use_cache: bool = True


INTENT_TTL_SECONDS = {
    "structured_operational": 300,
    "wiki_truth": 3600,
    "evidence_lookup": 120,
    "relationship_context": 900,
    "report_generation": 3600,
}

QUERY_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
QUERY_CACHE_MAX_ITEMS = 256


def _safe_uuid(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError):
        return None


def _log_query(user_id: Optional[str], query_text: str, query_type: str, tools_used: list[str], rows: int, chunks: int, summary: str):
    safe_user_id = _safe_uuid(user_id)
    execute(
        """
        insert into query_logs (user_id, query_text, query_type, tools_used, rows_returned, chunks_returned, response_summary)
        values (%s, %s, %s, %s, %s, %s, %s)
        """,
        (safe_user_id, query_text, query_type, tools_used, rows, chunks, summary),
    )


def _log_audit(user_id: Optional[str], action_type: str, table_name: str, record_id: Optional[str], previous: Optional[dict], new: Optional[dict]):
    safe_user_id = _safe_uuid(user_id)
    execute(
        """
        insert into audit_logs (user_id, action_type, table_name, record_id, previous_value, new_value)
        values (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
        """,
        (safe_user_id, action_type, table_name, record_id, _to_json(previous), _to_json(new)),
    )


def _to_json(value: Optional[dict]) -> str:
    import json

    return json.dumps(value or {})


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().split()).lower()


def _extract_entities(query: str) -> dict[str, Optional[str]]:
    normalized = _normalize_query(query)
    entities: dict[str, Optional[str]] = {
        "project": None,
        "client": None,
        "vendor": None,
        "business_unit": None,
    }

    project_patterns = [
        r"(?:/status|status|project|budget)\s+([a-z0-9_-]{2,20})",
        r"(?:status of|budget for|project status for)\s+([a-z0-9_-]{2,20})",
    ]
    for pattern in project_patterns:
        match = re.search(pattern, normalized)
        if match:
            entities["project"] = match.group(1).upper()
            break

    if not entities["project"]:
        for token in re.findall(r"\b[A-Z0-9]{2,10}\b", query):
            if token.lower() not in {"what", "show", "latest", "report", "vendor"}:
                entities["project"] = token.upper()
                break

    vendor_match = re.search(r"(?:/vendor|vendor)\s+(.+)", normalized)
    if vendor_match:
        entities["vendor"] = vendor_match.group(1).strip()

    client_match = re.search(r"(?:client)\s+([a-z0-9 _-]{2,60})", normalized)
    if client_match:
        entities["client"] = client_match.group(1).strip()

    business_unit_match = re.search(r"(?:business unit|bu)\s+([a-z0-9 _-]{2,60})", normalized)
    if business_unit_match:
        entities["business_unit"] = business_unit_match.group(1).strip()

    return entities


def _classify_query(query: str, entities: dict[str, Optional[str]]) -> dict[str, Any]:
    normalized = _normalize_query(query)

    if normalized.startswith("/report") or any(term in normalized for term in ["weekly report", "monthly report", "report weekly", "dashboard"]):
        return {"intent": "report_generation", "tool": "generate_report", "confidence": 0.95}

    if normalized.startswith("/wiki") or any(term in normalized for term in ["sop", "policy", "procedure", "approved process", "wiki"]):
        return {"intent": "wiki_truth", "tool": "search_wiki", "confidence": 0.93}

    if any(term in normalized for term in ["what did", "last discussion", "from meeting", "meeting note", "meeting notes", "client say", "transcript", "evidence"]):
        return {"intent": "evidence_lookup", "tool": "search_evidence", "confidence": 0.9}

    if any(term in normalized for term in ["history", "relationship", "recurring", "pattern", "context"]):
        return {"intent": "relationship_context", "tool": "relationship_context", "confidence": 0.85}

    if normalized.startswith("/budget") or "budget" in normalized:
        return {"intent": "structured_operational", "tool": "get_budget", "confidence": 0.94}

    if normalized.startswith("/vendor") or "vendor" in normalized:
        return {"intent": "structured_operational", "tool": "get_vendor", "confidence": 0.9}

    if normalized.startswith("/tasks") or any(term in normalized for term in ["action item", "action items", "task", "tasks me"]):
        return {"intent": "structured_operational", "tool": "get_action_items", "confidence": 0.88}

    if normalized.startswith("/status") or any(term in normalized for term in ["latest status", "project status", "status of"]):
        tool = "get_project" if entities.get("project") else "search_db"
        return {"intent": "structured_operational", "tool": tool, "confidence": 0.92}

    if entities.get("project"):
        return {"intent": "structured_operational", "tool": "get_project", "confidence": 0.84}

    return {"intent": "structured_operational", "tool": "search_db", "confidence": 0.7}


def _confidentiality_for_role(role: Optional[str]) -> str:
    role_normalized = (role or "").lower()
    if role_normalized in {"founder", "admin"}:
        return "secret"
    if role_normalized in {"manager", "lead"}:
        return "confidential"
    return "internal"


def _build_cache_key(user_id: Optional[str], role: Optional[str], intent: str, entities: dict[str, Optional[str]], query: str) -> str:
    entity_key = entities.get("project") or entities.get("vendor") or entities.get("client") or "none"
    query_hash = hashlib.sha1(_normalize_query(query).encode("utf-8")).hexdigest()[:16]
    return f"provaliant:{role or 'unknown'}:{user_id or 'anonymous'}:{intent}:{entity_key}:{query_hash}"


def _cache_get(cache_key: str) -> Optional[dict[str, Any]]:
    cached = QUERY_CACHE.get(cache_key)
    if not cached:
        return None
    expires_at, value = cached
    if expires_at < time.time():
        QUERY_CACHE.pop(cache_key, None)
        return None
    return value


def _cache_set(cache_key: str, ttl_seconds: int, value: dict[str, Any]) -> None:
    if len(QUERY_CACHE) >= QUERY_CACHE_MAX_ITEMS:
        oldest_key = min(QUERY_CACHE.items(), key=lambda item: item[1][0])[0]
        QUERY_CACHE.pop(oldest_key, None)
    QUERY_CACHE[cache_key] = (time.time() + ttl_seconds, value)


def _search_db_data(query: str, limit: int) -> list[dict[str, Any]]:
    q = f"%{query}%"
    return fetch_all(
        """
        select project_code, project_name, status, latest_summary, risk_level, gross_margin_percent, last_updated
        from projects
        where project_name ilike %s
           or project_code ilike %s
           or coalesce(latest_summary, '') ilike %s
        order by last_updated desc nulls last
        limit %s
        """,
        (q, q, q, limit),
    )


def _search_wiki_data(query: str, limit: int) -> list[dict[str, Any]]:
    q = f"%{query}%"
    return fetch_all(
        """
        select slug, title, category, summary, approval_status, last_reviewed_at, version, updated_at
        from wiki_pages
        where approval_status = 'approved'
          and (title ilike %s or coalesce(summary, '') ilike %s or coalesce(content, '') ilike %s)
        order by updated_at desc nulls last
        limit %s
        """,
        (q, q, q, limit),
    )


def _search_evidence_data(query: str, limit: int) -> list[dict[str, Any]]:
    q = f"%{query}%"
    return fetch_all(
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
        (q, limit),
    )


def _get_project_data(project_code_or_name: str) -> dict[str, Any]:
    q = f"%{project_code_or_name}%"
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

    actions: list[dict[str, Any]] = []
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

    return {
        "project": project,
        "open_action_items": actions,
    }


def _get_vendor_data(query: str, limit: int) -> list[dict[str, Any]]:
    q = f"%{query}%"
    return fetch_all(
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
        (q, q, q, limit),
    )


def _get_budget_data(project_code_or_name: str) -> dict[str, Any]:
    q = f"%{project_code_or_name}%"
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

    items: list[dict[str, Any]] = []
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

    return {
        "budget": budget,
        "items": items,
    }


def _get_action_items_data(query: str, limit: int) -> list[dict[str, Any]]:
    q = f"%{query}%"
    return fetch_all(
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
        (q, q, q, limit),
    )


def _generate_report_data(report_type: str) -> dict[str, Any]:
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

    return {
        "report_type": report_type,
        "projects": projects,
        "open_action_items": actions,
        "recent_meetings": meetings,
    }


def _collect_sources(tool_name: str, data: Any) -> list[str]:
    if tool_name == "get_project" and data.get("project"):
        return [f"project:{data['project'].get('project_code')}"]
    if tool_name == "search_db":
        return [f"project:{row.get('project_code')}" for row in data[:3] if row.get("project_code")]
    if tool_name == "search_wiki":
        return [f"wiki:{row.get('slug')}" for row in data[:3] if row.get("slug")]
    if tool_name == "search_evidence":
        return [f"document:{row.get('document_title')}" for row in data[:3] if row.get("document_title")]
    if tool_name == "get_vendor":
        return [f"vendor:{row.get('vendor_name')}" for row in data[:3] if row.get("vendor_name")]
    if tool_name == "generate_report":
        return [f"report:{data.get('report_type', 'report')}"]
    if tool_name == "get_budget" and data.get("budget"):
        return [f"budget:{data['budget'].get('id')}"]
    return []


def _format_answer(tool_name: str, data: Any) -> str:
    if tool_name == "get_project":
        project = data.get("project")
        if not project:
            return "Project tidak ditemukan."
        action_items = data.get("open_action_items", [])
        next_action = ""
        if action_items:
            first = action_items[0]
            next_action = f" Open action item utama: {first.get('task_text')} (priority {first.get('priority')}, due {first.get('due_date')})."
        return (
            f"{project.get('project_code')} ({project.get('project_name')}) status {project.get('status')}, "
            f"risk {project.get('risk_level')}, margin {project.get('gross_margin_percent')}%. "
            f"Update terbaru: {project.get('latest_summary')}." + next_action
        )
    if tool_name == "search_db":
        if not data:
            return "Tidak ada hasil structured DB yang cocok."
        summaries = [f"{row.get('project_code')} {row.get('status')}" for row in data[:3]]
        return "Hasil structured DB: " + "; ".join(summaries) + "."
    if tool_name == "search_wiki":
        if not data:
            return "Tidak ada halaman wiki approved yang cocok."
        top = data[0]
        return f"Wiki teratas: {top.get('title')} ({top.get('slug')}). Summary: {top.get('summary') or 'summary unavailable'}."
    if tool_name == "search_evidence":
        if not data:
            return "Tidak ada evidence chunk yang cocok."
        top = data[0]
        return f"Evidence teratas berasal dari {top.get('document_title')} dengan section {top.get('section_title') or 'n/a'}."
    if tool_name == "get_vendor":
        if not data:
            return "Vendor tidak ditemukan."
        top = data[0]
        return f"Vendor teratas: {top.get('vendor_name')} ({top.get('vendor_category') or 'category n/a'}), quality score {top.get('quality_score')}."
    if tool_name == "get_budget":
        budget = data.get("budget")
        if not budget:
            return "Budget project tidak ditemukan."
        items = data.get("items", [])
        return f"Budget ditemukan untuk project terkait dengan {len(items)} item dan status {budget.get('approval_status') or 'n/a'}."
    if tool_name == "get_action_items":
        if not data:
            return "Tidak ada action item yang cocok."
        top = data[0]
        return f"Action item terdekat: {top.get('task_text')} untuk project {top.get('project_code') or top.get('project_name') or 'n/a'}."
    if tool_name == "generate_report":
        return (
            f"Report {data.get('report_type')} berisi {len(data.get('projects', []))} project, "
            f"{len(data.get('open_action_items', []))} open action item, dan "
            f"{len(data.get('recent_meetings', []))} recent meeting."
        )
    return "Query selesai diproses."


def _run_brain_tool(tool_name: str, query: str, entities: dict[str, Optional[str]]) -> tuple[Any, list[str]]:
    if tool_name == "get_project":
        project_ref = entities.get("project") or query
        data = _get_project_data(project_ref)
        return data, ["get_project", "get_action_items"]
    if tool_name == "get_budget":
        project_ref = entities.get("project") or query
        data = _get_budget_data(project_ref)
        return data, ["get_budget"]
    if tool_name == "get_vendor":
        vendor_ref = entities.get("vendor") or query
        data = _get_vendor_data(vendor_ref, 10)
        return data, ["get_vendor"]
    if tool_name == "get_action_items":
        data = _get_action_items_data(query, 10)
        return data, ["get_action_items"]
    if tool_name == "search_wiki":
        data = _search_wiki_data(query, 10)
        return data, ["search_wiki"]
    if tool_name == "search_evidence":
        data = _search_evidence_data(query, 10)
        return data, ["search_evidence"]
    if tool_name == "generate_report":
        data = _generate_report_data(query)
        return data, ["generate_report"]
    if tool_name == "relationship_context":
        vendor_rows = _get_vendor_data(entities.get("vendor") or query, 5)
        evidence_rows = _search_evidence_data(query, 5)
        data = {
            "vendors": vendor_rows,
            "evidence": evidence_rows,
        }
        return data, ["get_vendor", "search_evidence"]
    data = _search_db_data(query, 10)
    return data, ["search_db"]


@app.get("/health")
def health(_: bool = Depends(require_auth)):
    return {
        "status": "ok",
        "service": "provaliant-brain-os",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/brain/query")
def brain_query(req: BrainQueryRequest, _: bool = Depends(require_auth)):
    entities = _extract_entities(req.query)
    route = _classify_query(req.query, entities)
    intent = route["intent"]
    tool_name = route["tool"]
    ttl_seconds = INTENT_TTL_SECONDS[intent]
    cache_key = _build_cache_key(req.user_id, req.role, intent, entities, req.query)

    cached = _cache_get(cache_key) if req.use_cache else None
    if cached:
        cached["cache"] = "hit"
        return cached

    data, tools_used = _run_brain_tool(tool_name, req.query, entities)

    if isinstance(data, list):
        rows_returned = len(data)
        chunks_returned = len(data) if tool_name == "search_evidence" else 0
    elif tool_name == "get_project":
        rows_returned = 1 if data.get("project") else 0
        chunks_returned = 0
    elif tool_name == "generate_report":
        rows_returned = len(data.get("projects", [])) + len(data.get("open_action_items", [])) + len(data.get("recent_meetings", []))
        chunks_returned = 0
    elif tool_name == "relationship_context":
        rows_returned = len(data.get("vendors", []))
        chunks_returned = len(data.get("evidence", []))
    else:
        rows_returned = 1 if data else 0
        chunks_returned = 0

    answer = _format_answer(tool_name, data)
    response = {
        "status": "ok",
        "intent": intent,
        "tool_used": tool_name,
        "cache": "miss",
        "cache_key": cache_key,
        "cache_policy": "short_ttl" if ttl_seconds <= 300 else "medium_ttl",
        "ttl_seconds": ttl_seconds,
        "entities": entities,
        "permission": {
            "needs_permission": True,
            "role": req.role,
            "confidentiality_max": _confidentiality_for_role(req.role),
        },
        "answer": answer,
        "sources": _collect_sources(tool_name, data),
        "data": data,
        "confidence": route["confidence"],
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }

    _log_query(req.user_id, req.query, intent, tools_used, rows_returned, chunks_returned, f"brain_query:{tool_name}")

    if req.use_cache and intent != "evidence_lookup":
        _cache_set(cache_key, ttl_seconds, response.copy())

    return response


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
    safe_user_id = _safe_uuid(req.user_id)
    page = fetch_one("select id, slug, content from wiki_pages where slug = %s", (req.slug,))

    if page:
        rows = execute(
            """
            insert into wiki_change_requests (wiki_page_id, proposed_content, change_reason, proposed_by, approval_status)
            values (%s, %s, %s, %s, 'pending_review')
            """,
            (page["id"], req.content, "Auto suggestion from MCP", safe_user_id),
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
