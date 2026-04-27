import os
from typing import Any, Iterable

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg2.connect(DATABASE_URL)


def fetch_all(query: str, params: Iterable[Any] = ()):  # list[dict]
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [dict(row) for row in cur.fetchall()]


def fetch_one(query: str, params: Iterable[Any] = ()):  # dict | None
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            row = cur.fetchone()
            return dict(row) if row else None


def execute(query: str, params: Iterable[Any] = ()):  # int
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            conn.commit()
            return cur.rowcount
