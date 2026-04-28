import hashlib
import re
import time
from datetime import date, datetime, timedelta
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


class IngestRequest(RequestContext):
    channel: str = "telegram"
    raw_text: str
    entry_type: Optional[str] = None
    extracted: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None
    source_type: str = "chat"
    source_name: Optional[str] = None


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

    return json.dumps(value or {}, default=str)


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
        r"(?:status of|budget for|project status for)\s+([a-z0-9_-]{2,20})",
        r"(?:/status|/budget)\s+([a-z0-9_-]{2,20})",
        r"(?:project|budget)\s+([a-z0-9_-]{2,20})",
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


SUPPORTED_INGEST_ENTRY_TYPES = {"meeting", "vendor_quote", "budget", "project_update", "contact"}


def _extract_kv_pairs(raw_text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in raw_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = re.sub(r"[^a-z0-9_]+", "_", key.strip().lower())
        if normalized_key:
            pairs[normalized_key] = value.strip()
    return pairs


def _parse_money(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    raw = value.strip().lower().replace(",", ".")
    number_match = re.search(r"(\d+(?:\.\d+)?)", raw)
    if not number_match:
        return None
    amount = float(number_match.group(1))
    if any(unit in raw for unit in ["jt", "juta", "mio"]):
        return amount * 1_000_000
    if any(unit in raw for unit in ["rb", "ribu", "k"]):
        return amount * 1_000
    return amount


def _extract_first_money(raw_text: str) -> Optional[float]:
    match = re.search(r"\b\d+(?:[.,]\d+)?\s*(?:jt|juta|rb|ribu|k)?\b", raw_text, flags=re.IGNORECASE)
    if not match:
        return None
    return _parse_money(match.group(0))


def _parse_due_date(raw_text: str) -> Optional[date]:
    normalized = raw_text.lower()
    today = datetime.utcnow().date()

    if "besok" in normalized or "tomorrow" in normalized:
        return today + timedelta(days=1)

    weekdays = {
        "senin": 0,
        "monday": 0,
        "selasa": 1,
        "tuesday": 1,
        "rabu": 2,
        "wednesday": 2,
        "kamis": 3,
        "thursday": 3,
        "jumat": 4,
        "friday": 4,
        "sabtu": 5,
        "saturday": 5,
        "minggu": 6,
        "sunday": 6,
    }
    for token, weekday in weekdays.items():
        if re.search(rf"\b{re.escape(token)}\b", normalized):
            delta = (weekday - today.weekday()) % 7
            if delta == 0:
                delta = 7
            return today + timedelta(days=delta)

    explicit_iso = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", raw_text)
    if explicit_iso:
        try:
            return datetime.strptime(explicit_iso.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None

    explicit_dmy = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", raw_text)
    if explicit_dmy:
        try:
            return date(int(explicit_dmy.group(3)), int(explicit_dmy.group(2)), int(explicit_dmy.group(1)))
        except ValueError:
            return None

    return None


def _extract_entry_type(raw_text: str, explicit_entry_type: Optional[str]) -> tuple[Optional[str], float]:
    if explicit_entry_type:
        normalized = explicit_entry_type.strip().lower()
        if normalized in SUPPORTED_INGEST_ENTRY_TYPES:
            return normalized, 0.99

    command_match = re.search(r"/entry\s+([a-z_]+)", raw_text.lower())
    if command_match:
        detected = command_match.group(1).strip()
        if detected in SUPPORTED_INGEST_ENTRY_TYPES:
            return detected, 0.98

    rules = {
        "meeting": ["meeting", "mom", "notulen", "rapat", "decision", "action item", "discussed", "agreed"],
        "vendor_quote": ["vendor", "quote", "quotation", "harga", "penawaran", "lead time", "produksi", "booth", "printing"],
        "budget": ["budget", "internal", "external", "margin", "profit", "cost", "realisasi", "rab"],
        "project_update": ["status", "update", "blocker", "issue", "delay", "risk", "next step"],
        "contact": ["contact", "pic", "phone", "email", "whatsapp", "client person"],
    }
    normalized = raw_text.lower()
    scored = []
    for entry_type, keywords in rules.items():
        score = sum(1 for keyword in keywords if keyword in normalized)
        scored.append((score, entry_type))

    scored.sort(reverse=True)
    best_score, best_type = scored[0]
    if best_score <= 0:
        return None, 0.0
    confidence = min(0.8 + (best_score * 0.03), 0.95)
    return best_type, confidence


def _get_kv_value(pairs: dict[str, str], *keys: str) -> Optional[str]:
    for key in keys:
        if key in pairs and pairs[key]:
            return pairs[key]
    return None


def _extract_with_pattern(raw_text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, raw_text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _extract_ingest_payload(entry_type: str, raw_text: str) -> dict[str, Any]:
    pairs = _extract_kv_pairs(raw_text)
    project = _get_kv_value(pairs, "project") or _extract_with_pattern(raw_text, r"\bproject\s+([a-z0-9_-]{2,30})")
    client = _get_kv_value(pairs, "client")
    vendor = _get_kv_value(pairs, "vendor")

    payload: dict[str, Any] = {
        "project": project.upper() if project else None,
        "client": client,
        "vendor": vendor,
    }

    if entry_type == "meeting":
        action_text = _get_kv_value(pairs, "action", "action_item")
        if not action_text:
            action_text = _extract_with_pattern(raw_text, r"\baction\s*:?\s*(.+)")
        decision_text = _get_kv_value(pairs, "decision")
        if not decision_text:
            decision_text = _extract_with_pattern(raw_text, r"\bdecision\s*:?\s*(.+?)(?:\baction\b|$)")
        summary_text = _get_kv_value(pairs, "summary")
        if not summary_text and decision_text:
            summary_text = decision_text
        payload.update(
            {
                "summary": summary_text,
                "decision": decision_text,
                "action": action_text,
                "action_owner": _extract_with_pattern(action_text or "", r"^\s*([a-zA-Z][a-zA-Z0-9_-]{1,30})"),
                "due_date": _parse_due_date(action_text or raw_text),
            }
        )
        return payload

    if entry_type == "vendor_quote":
        if not vendor:
            vendor = _extract_with_pattern(raw_text, r"\bvendor\s+(.+?)(?:\bitem\b|\bprice\b|\bharga\b|\blead\s*time\b|\bproject\b|\bbooth\b|\bprinting\b|\bstage\b|\d)")
        lead_time_text = _get_kv_value(pairs, "lead_time", "leadtime")
        if not lead_time_text:
            lead_time_text = _extract_with_pattern(raw_text, r"lead\s*time\s*(\d+)")
        lead_time_days = int(lead_time_text) if lead_time_text and lead_time_text.isdigit() else None
        item_text = _get_kv_value(pairs, "item") or _extract_with_pattern(raw_text, r"\bitem\s*:?\s*([^\n]+)")
        if not item_text:
            item_text = _extract_with_pattern(raw_text, r"\b(booth|printing|stage setup|production)\b")
        payload.update(
            {
                "vendor": vendor.strip() if vendor else vendor,
                "item": item_text,
                "price": _parse_money(_get_kv_value(pairs, "price", "harga", "penawaran") or _extract_with_pattern(raw_text, r"\b(?:price|harga)\s*:?\s*([^\n]+)")) or _extract_first_money(raw_text),
                "lead_time_days": lead_time_days,
            }
        )
        return payload

    if entry_type == "budget":
        if not vendor:
            vendor = _extract_with_pattern(raw_text, r"\bvendor\s+(.+?)(?:\bitem\b|\binternal\b|\bexternal\b|$)")
        internal_raw = _get_kv_value(pairs, "internal", "internal_total")
        external_raw = _get_kv_value(pairs, "external", "external_total")
        payload.update(
            {
                "vendor": vendor.strip() if vendor else vendor,
                "item": _get_kv_value(pairs, "item") or _extract_with_pattern(raw_text, r"\bitem\s*:?\s*([^\n]+)"),
                "internal_total": _parse_money(internal_raw) or _parse_money(_extract_with_pattern(raw_text, r"\binternal\s*:?\s*([^\n]+)")),
                "external_total": _parse_money(external_raw) or _parse_money(_extract_with_pattern(raw_text, r"\bexternal\s*:?\s*([^\n]+)")),
            }
        )
        return payload

    if entry_type == "project_update":
        payload.update(
            {
                "status": _get_kv_value(pairs, "status") or _extract_with_pattern(raw_text, r"\bstatus\s*:?\s*([^\n]+)"),
                "issue": _get_kv_value(pairs, "issue", "blocker", "blockers") or _extract_with_pattern(raw_text, r"\b(?:issue|blocker|risk)\s*:?\s*([^\n]+?)(?:\bnext\s*step\b|$)"),
                "next_step": _get_kv_value(pairs, "next_step", "next_steps") or _extract_with_pattern(raw_text, r"\bnext\s*step\s*:?\s*([^\n]+)"),
            }
        )
        return payload

    if entry_type == "contact":
        payload.update(
            {
                "name": _get_kv_value(pairs, "name", "full_name", "pic") or _extract_with_pattern(raw_text, r"\b(?:contact|pic)\s*:?\s*([a-zA-Z][^\n,;]+)"),
                "phone": _get_kv_value(pairs, "phone", "whatsapp"),
                "email": _get_kv_value(pairs, "email"),
            }
        )
        return payload

    return payload


def _validate_ingest_payload(entry_type: str, extracted: dict[str, Any], classifier_confidence: float, provided_confidence: Optional[float]) -> tuple[float, list[str]]:
    required_map = {
        "meeting": ["project", "decision", "action", "action_owner", "due_date"],
        "vendor_quote": ["project", "vendor", "item", "price"],
        "budget": ["project", "item", "internal_total", "external_total", "vendor"],
        "project_update": ["project", "status", "issue", "next_step"],
        "contact": ["name"],
    }
    required = required_map.get(entry_type, [])
    missing_fields: list[str] = []
    for field_name in required:
        value = extracted.get(field_name)
        if value is None:
            missing_fields.append(field_name)
            continue
        if isinstance(value, str) and not value.strip():
            missing_fields.append(field_name)

    confidence = classifier_confidence
    if not missing_fields:
        confidence = max(confidence, 0.92)
    else:
        confidence = max(0.45, confidence - (0.12 * len(missing_fields)))

    if provided_confidence is not None:
        confidence = min(confidence, max(0.0, min(1.0, provided_confidence)))

    return round(confidence, 2), missing_fields


def _find_or_create_project(project_ref: str) -> dict[str, Any]:
    project = fetch_one(
        """
        select id, project_code, project_name, status, risk_level
        from projects
        where project_code ilike %s or project_name ilike %s
        order by updated_at desc nulls last
        limit 1
        """,
        (project_ref, project_ref),
    )
    if project:
        return project

    code = project_ref.upper()
    created = fetch_one(
        """
        insert into projects (project_code, project_name, status, last_updated)
        values (%s, %s, 'active', now())
        returning id, project_code, project_name, status, risk_level
        """,
        (code, code),
    )
    return created


def _ensure_entity(entity_type: str, display_name: str) -> dict[str, Any]:
    normalized_name = re.sub(r"[^a-z0-9]+", "_", display_name.lower()).strip("_")[:120] or display_name.lower()
    return fetch_one(
        """
        insert into entities (entity_type, name, display_name)
        values (%s, %s, %s)
        on conflict (entity_type, name)
        do update set display_name = excluded.display_name, updated_at = now()
        returning id, entity_type, name, display_name
        """,
        (entity_type, normalized_name, display_name),
    )


def _ensure_vendor(vendor_name: str) -> dict[str, Any]:
    entity = _ensure_entity("vendor", vendor_name)
    vendor = fetch_one(
        """
        insert into vendors (entity_id, vendor_category)
        values (%s, 'general')
        on conflict (entity_id)
        do update set updated_at = now()
        returning id, entity_id, vendor_category
        """,
        (entity["id"],),
    )
    vendor["vendor_name"] = entity["display_name"]
    return vendor


def _find_or_create_client(client_name: str) -> dict[str, Any]:
    existing = fetch_one(
        """
        select c.id, c.entity_id, e.display_name
        from clients c
        join entities e on e.id = c.entity_id
        where e.display_name ilike %s
        order by c.updated_at desc nulls last
        limit 1
        """,
        (client_name,),
    )
    if existing:
        return existing

    entity = _ensure_entity("client", client_name)
    return fetch_one(
        """
        insert into clients (entity_id, relationship_status)
        values (%s, 'active')
        on conflict (entity_id)
        do update set updated_at = now()
        returning id, entity_id
        """,
        (entity["id"],),
    )


def _create_source(req: IngestRequest, entry_type: str, extracted: dict[str, Any]) -> dict[str, Any]:
    return fetch_one(
        """
        insert into sources (source_type, source_name, channel_name, sender_identifier, raw_reference, metadata)
        values (%s, %s, %s, %s, %s, %s::jsonb)
        returning id, source_type, source_name, channel_name
        """,
        (
            req.source_type,
            req.source_name or f"{req.channel}_ingest",
            req.channel,
            req.user_id,
            req.raw_text,
            _to_json({"entry_type": entry_type, "extracted": extracted, "role": req.role}),
        ),
    )


def _write_project_update(req: IngestRequest, extracted: dict[str, Any], source_id: str) -> dict[str, Any]:
    project = _find_or_create_project(extracted["project"])
    row = fetch_one(
        """
        insert into project_updates (project_id, update_date, update_type, status, summary, blockers, next_steps, source_id, confidence)
        values (%s, now(), 'manager_entry', %s, %s, %s, %s, %s, %s)
        returning id, project_id, status
        """,
        (
            project["id"],
            extracted.get("status"),
            extracted.get("issue"),
            extracted.get("issue"),
            extracted.get("next_step"),
            source_id,
            extracted.get("confidence"),
        ),
    )
    execute(
        """
        update projects
        set status = coalesce(%s, status),
            risk_level = case when lower(coalesce(%s, '')) like '%%risk%%' then 'high' else risk_level end,
            latest_summary = coalesce(%s, latest_summary),
            last_updated = now()
        where id = %s
        """,
        (extracted.get("status"), extracted.get("status"), extracted.get("issue"), project["id"]),
    )
    return {
        "project_id": project["id"],
        "project_code": project.get("project_code"),
        "project_update_id": row["id"],
    }


def _write_vendor_quote(req: IngestRequest, extracted: dict[str, Any], source_id: str) -> dict[str, Any]:
    vendor = _ensure_vendor(extracted["vendor"])
    if extracted.get("project"):
        _find_or_create_project(extracted["project"])
    ratecard = fetch_one(
        """
        insert into ratecards (vendor_id, item_name, item_category, external_price, lead_time_days, approval_status)
        values (%s, %s, 'vendor_quote', %s, %s, 'pending_review')
        returning id, vendor_id, approval_status
        """,
        (
            vendor["id"],
            extracted.get("item"),
            extracted.get("price"),
            extracted.get("lead_time_days"),
        ),
    )
    return {
        "vendor_id": vendor["id"],
        "vendor": vendor["vendor_name"],
        "ratecard_id": ratecard["id"],
    }


def _write_budget(req: IngestRequest, extracted: dict[str, Any], source_id: str) -> dict[str, Any]:
    project = _find_or_create_project(extracted["project"])
    vendor_id = None
    if extracted.get("vendor"):
        vendor_id = _ensure_vendor(extracted["vendor"])["id"]

    total_internal = extracted.get("internal_total")
    total_external = extracted.get("external_total")
    total_profit = None
    profit_percent = None
    if total_internal is not None and total_external is not None:
        total_profit = total_external - total_internal
        if total_external:
            profit_percent = round((total_profit / total_external) * 100, 2)

    budget_version = f"entry-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    budget = fetch_one(
        """
        insert into budgets (project_id, budget_version, budget_status, total_internal, total_external, total_profit, profit_percent)
        values (%s, %s, 'draft', %s, %s, %s, %s)
        returning id, budget_version
        """,
        (project["id"], budget_version, total_internal, total_external, total_profit, profit_percent),
    )

    item = fetch_one(
        """
        insert into budget_items (budget_id, item_category, item_name, internal_total, external_total, profit, profit_percent, vendor_id)
        values (%s, 'manual_entry', %s, %s, %s, %s, %s, %s)
        returning id, budget_id
        """,
        (budget["id"], extracted.get("item"), total_internal, total_external, total_profit, profit_percent, vendor_id),
    )
    return {
        "project_id": project["id"],
        "vendor_id": vendor_id,
        "budget_id": budget["id"],
        "budget_item_id": item["id"],
        "budget_version": budget["budget_version"],
    }


def _write_meeting(req: IngestRequest, extracted: dict[str, Any], source_id: str) -> dict[str, Any]:
    project = _find_or_create_project(extracted["project"])
    client_id = None
    if extracted.get("client"):
        client_id = _find_or_create_client(extracted["client"])["id"]

    meeting = fetch_one(
        """
        insert into meetings (meeting_title, meeting_date, client_id, project_id, summary)
        values (%s, now(), %s, %s, %s)
        returning id
        """,
        (f"Entry meeting {project.get('project_code')}", client_id, project["id"], extracted.get("summary")),
    )
    decision = fetch_one(
        """
        insert into decisions (meeting_id, project_id, decision_text, decision_date, confidence)
        values (%s, %s, %s, current_date, %s)
        returning id
        """,
        (meeting["id"], project["id"], extracted.get("decision"), extracted.get("confidence")),
    )
    action = fetch_one(
        """
        insert into action_items (meeting_id, project_id, task_text, due_date, status, priority, source_id)
        values (%s, %s, %s, %s, 'open', 'high', %s)
        returning id
        """,
        (meeting["id"], project["id"], extracted.get("action"), extracted.get("due_date"), source_id),
    )
    project_update = fetch_one(
        """
        insert into project_updates (project_id, update_date, update_type, status, summary, blockers, next_steps, source_id, confidence)
        values (%s, now(), 'meeting_summary', 'at_risk', %s, %s, %s, %s, %s)
        returning id
        """,
        (
            project["id"],
            extracted.get("summary"),
            extracted.get("summary"),
            extracted.get("action"),
            source_id,
            extracted.get("confidence"),
        ),
    )
    return {
        "meeting_id": meeting["id"],
        "decision_id": decision["id"],
        "action_item_id": action["id"],
        "project_update_id": project_update["id"],
    }


def _write_contact(req: IngestRequest, extracted: dict[str, Any], source_id: str) -> dict[str, Any]:
    entity = _ensure_entity("person", extracted["name"])
    client_id = None
    if extracted.get("client"):
        client_id = _find_or_create_client(extracted["client"])["id"]
    contact = fetch_one(
        """
        insert into contacts (entity_id, client_id, full_name, company, phone, email, whatsapp, confidentiality, notes)
        values (%s, %s, %s, %s, %s, %s, %s, 'internal', %s)
        returning id, full_name
        """,
        (
            entity["id"],
            client_id,
            extracted["name"],
            extracted.get("client"),
            extracted.get("phone"),
            extracted.get("email"),
            extracted.get("phone"),
            f"source_id:{source_id}",
        ),
    )
    return {
        "entity_id": entity["id"],
        "contact_id": contact["id"],
        "contact_name": contact["full_name"],
    }


def _write_ingest_records(req: IngestRequest, entry_type: str, extracted: dict[str, Any]) -> dict[str, Any]:
    source = _create_source(req, entry_type, extracted)
    _log_audit(req.user_id, "insert", "sources", source["id"], None, source)

    if entry_type == "project_update":
        records = _write_project_update(req, extracted, source["id"])
        _log_audit(req.user_id, "update", "projects", records["project_id"], None, records)
        _log_audit(req.user_id, "insert", "project_updates", records["project_update_id"], None, records)
        return records
    if entry_type == "vendor_quote":
        records = _write_vendor_quote(req, extracted, source["id"])
        _log_audit(req.user_id, "upsert", "vendors", records["vendor_id"], None, records)
        _log_audit(req.user_id, "insert", "ratecards", records["ratecard_id"], None, records)
        return records
    if entry_type == "budget":
        records = _write_budget(req, extracted, source["id"])
        _log_audit(req.user_id, "upsert", "projects", records["project_id"], None, records)
        if records.get("vendor_id"):
            _log_audit(req.user_id, "upsert", "vendors", records["vendor_id"], None, records)
        _log_audit(req.user_id, "insert", "budgets", records["budget_id"], None, records)
        _log_audit(req.user_id, "insert", "budget_items", records["budget_item_id"], None, records)
        return records
    if entry_type == "meeting":
        records = _write_meeting(req, extracted, source["id"])
        _log_audit(req.user_id, "insert", "meetings", records["meeting_id"], None, records)
        _log_audit(req.user_id, "insert", "decisions", records["decision_id"], None, records)
        _log_audit(req.user_id, "insert", "action_items", records["action_item_id"], None, records)
        _log_audit(req.user_id, "insert", "project_updates", records["project_update_id"], None, records)
        return records
    if entry_type == "contact":
        records = _write_contact(req, extracted, source["id"])
        _log_audit(req.user_id, "upsert", "entities", records["entity_id"], None, records)
        _log_audit(req.user_id, "insert", "contacts", records["contact_id"], None, records)
        return records

    raise ValueError(f"Unsupported entry_type: {entry_type}")


def _ingest_message(entry_type: str, records_created: dict[str, Any]) -> str:
    if entry_type == "vendor_quote":
        return "Vendor quote saved as pending approval."
    if entry_type == "project_update":
        return f"Project {records_created.get('project_code', '')} updated."
    if entry_type == "meeting":
        return "Meeting saved. 1 decision and 1 action item created."
    if entry_type == "budget":
        return "Budget entry saved as draft."
    if entry_type == "contact":
        return "Contact saved."
    return "Entry saved."


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


@app.post("/ingest")
def ingest(req: IngestRequest, _: bool = Depends(require_auth)):
    entry_type, classifier_confidence = _extract_entry_type(req.raw_text, req.entry_type)
    if not entry_type:
        return {
            "status": "needs_confirmation",
            "entry_type": None,
            "confidence": 0.0,
            "missing_fields": ["entry_type"],
            "message": "Entry type belum jelas. Gunakan /entry meeting, /entry vendor_quote, /entry budget, /entry project_update, atau /entry contact.",
        }

    extracted = req.extracted if req.extracted else _extract_ingest_payload(entry_type, req.raw_text)
    confidence, missing_fields = _validate_ingest_payload(entry_type, extracted, classifier_confidence, req.confidence)
    extracted["confidence"] = confidence
    extracted["confidentiality"] = (
        "confidential"
        if entry_type in {"vendor_quote", "budget"}
        else "restricted"
        if any(term in req.raw_text.lower() for term in ["legal", "ip", "nda", "patent"])
        else "internal"
    )

    if confidence < 0.85:
        return {
            "status": "needs_confirmation",
            "entry_type": entry_type,
            "confidence": confidence,
            "extracted": extracted,
            "missing_fields": missing_fields,
            "message": f"Mohon lengkapi field: {', '.join(missing_fields)}.",
        }

    records_created = _write_ingest_records(req, entry_type, extracted)
    _log_query(
        req.user_id,
        req.raw_text,
        "ingestion",
        ["ingest", entry_type],
        len(records_created),
        0,
        f"ingest:{entry_type}",
    )
    return {
        "status": "saved",
        "entry_type": entry_type,
        "confidence": confidence,
        "records_created": records_created,
        "message": _ingest_message(entry_type, records_created),
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
