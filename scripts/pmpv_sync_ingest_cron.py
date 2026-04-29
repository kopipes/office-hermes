#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required env: {name}")
    return value


def http_json(url: str, headers: dict[str, str], method: str = "GET", body: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=45) as resp:
            code = resp.getcode()
            content = resp.read().decode("utf-8")
            parsed = json.loads(content) if content else {}
            return code, parsed
    except error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = str(exc)
        return exc.code, {"error": detail}


def ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        create table if not exists moms (
          id text primary key,
          title text,
          meeting_date text,
          client_name text,
          raw_json text not null,
          synced_at text not null
        )
        """
    )
    cur.execute(
        """
        create table if not exists projects (
          id text primary key,
          project_number text,
          title text,
          status text,
          raw_json text not null,
          synced_at text not null
        )
        """
    )
    cur.execute(
        """
        create table if not exists sync_meta (
          k text primary key,
          v text
        )
        """
    )
    cur.execute(
        """
        create table if not exists ingested_markers (
          kind text not null,
          record_id text not null,
          fingerprint text not null,
          ingested_at text not null,
          primary key(kind, record_id)
        )
        """
    )
    conn.commit()


def ensure_table_columns(conn: sqlite3.Connection, table_name: str, expected: dict[str, str]) -> None:
    cur = conn.cursor()
    rows = cur.execute(f"pragma table_info({table_name})").fetchall()
    cols = {row[1] for row in rows}
    for col, definition in expected.items():
        if col in cols:
            continue
        cur.execute(f"alter table {table_name} add column {col} {definition}")
    conn.commit()


def get_project_number_column(conn: sqlite3.Connection) -> str:
    cur = conn.cursor()
    rows = cur.execute("pragma table_info(projects)").fetchall()
    cols = {row[1] for row in rows}
    if "project_number" in cols:
        return "project_number"
    if "number" in cols:
        return "number"
    cur.execute("alter table projects add column number text")
    conn.commit()
    return "number"


def upsert_cache(conn: sqlite3.Connection, moms: list[dict[str, Any]], projects: list[dict[str, Any]]) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    ensure_table_columns(
        conn,
        "moms",
        {
            "title": "text",
            "meeting_date": "text",
            "client_name": "text",
            "raw_json": "text",
            "synced_at": "text",
        },
    )
    ensure_table_columns(
        conn,
        "projects",
        {
            "title": "text",
            "status": "text",
            "raw_json": "text",
            "synced_at": "text",
        },
    )
    project_number_column = get_project_number_column(conn)
    for mom in moms:
        cur.execute(
            """
            insert into moms (id, title, meeting_date, client_name, raw_json, synced_at)
            values (?, ?, ?, ?, ?, ?)
            on conflict(id) do update set
              title=excluded.title,
              meeting_date=excluded.meeting_date,
              client_name=excluded.client_name,
              raw_json=excluded.raw_json,
              synced_at=excluded.synced_at
            """,
            (
                str(mom.get("id") or ""),
                mom.get("title"),
                mom.get("date"),
                mom.get("clientName"),
                json.dumps(mom, ensure_ascii=False),
                now_iso,
            ),
        )
    for proj in projects:
        cur.execute(
            f"""
            insert into projects (id, {project_number_column}, title, status, raw_json, synced_at)
            values (?, ?, ?, ?, ?, ?)
            on conflict(id) do update set
              {project_number_column}=excluded.{project_number_column},
              title=excluded.title,
              status=excluded.status,
              raw_json=excluded.raw_json,
              synced_at=excluded.synced_at
            """,
            (
                str(proj.get("id") or ""),
                proj.get("projectNumber") or proj.get("number"),
                proj.get("title"),
                proj.get("status"),
                json.dumps(proj, ensure_ascii=False),
                now_iso,
            ),
        )
    cur.execute("insert or replace into sync_meta (k, v) values ('last_sync_iso', ?)", (now_iso,))
    cur.execute("insert or replace into sync_meta (k, v) values ('moms_count', ?)", (str(len(moms)),))
    cur.execute("insert or replace into sync_meta (k, v) values ('projects_count', ?)", (str(len(projects)),))
    conn.commit()


def text_from_any(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        parts = []
        for item in value:
            t = text_from_any(item)
            if t:
                parts.append(t)
        return "; ".join(parts)
    return str(value).strip()


def clean_for_entry(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def fingerprint(record: dict[str, Any]) -> str:
    candidate = record.get("updatedAt") or record.get("createdAt")
    if candidate:
        return str(candidate)
    normalized = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def should_ingest(conn: sqlite3.Connection, kind: str, record_id: str, fp: str) -> bool:
    cur = conn.cursor()
    row = cur.execute(
        "select fingerprint from ingested_markers where kind = ? and record_id = ?",
        (kind, record_id),
    ).fetchone()
    if not row:
        return True
    return row[0] != fp


def mark_ingested(conn: sqlite3.Connection, kind: str, record_id: str, fp: str) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute(
        """
        insert into ingested_markers (kind, record_id, fingerprint, ingested_at)
        values (?, ?, ?, ?)
        on conflict(kind, record_id) do update set
          fingerprint=excluded.fingerprint,
          ingested_at=excluded.ingested_at
        """,
        (kind, record_id, fp, now_iso),
    )
    conn.commit()


def ingest_entry(mcp_base: str, mcp_api_key: str, raw_text: str) -> tuple[int, dict[str, Any]]:
    code, payload = http_json(
        f"{mcp_base}/ingest",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mcp_api_key}",
        },
        method="POST",
        body={
            "user_id": "pmpv_sync_bot",
            "role": "manager",
            "channel": "pmpv_api",
            "raw_text": raw_text,
        },
    )
    return code, payload if isinstance(payload, dict) else {"raw": payload}


def build_meeting_entry(mom: dict[str, Any], project_number_by_id: dict[str, str]) -> str:
    project_ref = project_number_by_id.get(str(mom.get("projectId") or ""), "PMPV")
    client = clean_for_entry(text_from_any(mom.get("clientName")) or "Unknown Client")
    decision = clean_for_entry(text_from_any(mom.get("decisions")) or text_from_any(mom.get("topic")) or "Review MOM updates")
    action = clean_for_entry(text_from_any(mom.get("actionItems")) or "Ops follow up tomorrow")
    if not re.search(r"\b(tomorrow|besok|monday|tuesday|wednesday|thursday|friday|saturday|sunday|senin|selasa|rabu|kamis|jumat|sabtu|minggu)\b", action, flags=re.IGNORECASE):
        action = f"{action} tomorrow"
    return f"/entry meeting Project {project_ref} Client {client} Decision {decision} Action {action}"


def build_project_update_entry(project: dict[str, Any]) -> str:
    project_ref = clean_for_entry(str(project.get("projectNumber") or project.get("number") or project.get("id") or "PMPV"))
    status = clean_for_entry(text_from_any(project.get("status")) or "active")
    issue = clean_for_entry(text_from_any(project.get("description")) or "PMPV sync update")
    next_step = "review PMPV project board tomorrow"
    return f"/entry project_update Project {project_ref} Status {status} Issue {issue} Next step {next_step}"


def main() -> None:
    load_env_file(Path.home() / ".hermes" / ".env")
    load_env_file(Path.home() / "office-hermes" / ".env")

    pmpv_base = require_env("PMPV_BASE_URL").rstrip("/")
    pmpv_key = require_env("PMPV_INTERNAL_API_KEY")
    mcp_host = require_env("MCP_HOST")
    mcp_port = require_env("MCP_PORT")
    mcp_api_key = require_env("MCP_API_KEY")
    batch_size = int(os.environ.get("PMPV_SYNC_BATCH_SIZE", "100"))
    cache_path = Path(os.environ.get("PMPV_CACHE_PATH", str(Path.home() / ".hermes" / "data" / "pmpv-cache.sqlite")))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    raw_dir = cache_path.parent / "pmpv-raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    mcp_base = f"http://{mcp_host}:{mcp_port}"

    headers = {
        "x-internal-api-key": pmpv_key,
        "accept": "application/json",
    }

    moms_code, moms_payload = http_json(f"{pmpv_base}/api/integration/moms", headers)
    projects_code, projects_payload = http_json(f"{pmpv_base}/api/integration/projects", headers)
    export_code, export_payload = http_json(f"{pmpv_base}/api/integration/database/export", headers)

    if moms_code != 200 or projects_code != 200 or export_code != 200:
        raise RuntimeError(
            f"PMPV API error moms={moms_code} projects={projects_code} export={export_code}"
        )

    moms = moms_payload.get("moms", []) if isinstance(moms_payload, dict) else []
    projects = projects_payload.get("projects", []) if isinstance(projects_payload, dict) else []

    (raw_dir / "moms.json").write_text(json.dumps(moms_payload, ensure_ascii=False))
    (raw_dir / "projects.json").write_text(json.dumps(projects_payload, ensure_ascii=False))
    (raw_dir / "export.json").write_text(json.dumps(export_payload, ensure_ascii=False))

    conn = sqlite3.connect(cache_path)
    ensure_schema(conn)
    upsert_cache(conn, moms, projects)

    project_number_by_id = {
        str(p.get("id") or ""): str(p.get("projectNumber") or p.get("number") or p.get("id") or "PMPV")
        for p in projects
    }

    ingested_moms = 0
    ingested_projects = 0

    for mom in moms[:batch_size]:
        record_id = str(mom.get("id") or "")
        if not record_id:
            continue
        fp = fingerprint(mom)
        if not should_ingest(conn, "mom", record_id, fp):
            continue
        raw_text = build_meeting_entry(mom, project_number_by_id)
        code, payload = ingest_entry(mcp_base, mcp_api_key, raw_text)
        if code == 200 and payload.get("status") == "saved":
            mark_ingested(conn, "mom", record_id, fp)
            ingested_moms += 1

    for project in projects[:batch_size]:
        record_id = str(project.get("id") or "")
        if not record_id:
            continue
        fp = fingerprint(project)
        if not should_ingest(conn, "project", record_id, fp):
            continue
        raw_text = build_project_update_entry(project)
        code, payload = ingest_entry(mcp_base, mcp_api_key, raw_text)
        if code == 200 and payload.get("status") == "saved":
            mark_ingested(conn, "project", record_id, fp)
            ingested_projects += 1

    print(
        json.dumps(
            {
                "status": "ok",
                "synced": {
                    "moms": len(moms),
                    "projects": len(projects),
                },
                "ingested": {
                    "meetings_from_moms": ingested_moms,
                    "project_updates_from_projects": ingested_projects,
                },
                "cache_path": str(cache_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
