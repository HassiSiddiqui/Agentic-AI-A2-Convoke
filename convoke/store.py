from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from convoke.audit import utcnow
from convoke.paths import STORE, ensure_dirs

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    organizer_id TEXT NOT NULL,
    title TEXT NOT NULL,
    venue TEXT,
    event_date TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    name TEXT NOT NULL,
    room TEXT,
    starts_at TEXT,
    ends_at TEXT,
    capacity INTEGER NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_current INTEGER NOT NULL DEFAULT 1,
    superseded_at TEXT,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS session_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    approved_by TEXT,
    changed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS participants (
    participant_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT,
    preference TEXT,
    dietary TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (event_id, participant_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS allocations (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    cycle_id INTEGER NOT NULL,
    session_id TEXT,
    participant_id TEXT NOT NULL,
    requested_session TEXT,
    agent_status TEXT NOT NULL,
    organizer_status TEXT,
    organizer_comment TEXT,
    evidence TEXT,
    blocker TEXT,
    next_action TEXT,
    last_contact TEXT,
    is_current INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(event_id, cycle_id, participant_id)
);

CREATE TABLE IF NOT EXISTS waitlist (
    wait_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    participant_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    reason TEXT,
    is_current INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notices (
    notice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotency_key TEXT NOT NULL UNIQUE,
    event_id TEXT NOT NULL,
    participant_id TEXT,
    cycle_id INTEGER,
    subject TEXT,
    body TEXT,
    recipient TEXT,
    status TEXT NOT NULL,
    delivery_outcome TEXT,
    approved INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_sources (
    source_hash TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    filename TEXT,
    kind TEXT,
    flagged_injection INTEGER NOT NULL DEFAULT 0,
    processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS working_state (
    event_id TEXT PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    current_goal TEXT,
    plan_json TEXT,
    pending_question TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT,
    cycle_id INTEGER,
    timestamp TEXT NOT NULL,
    kind TEXT NOT NULL,
    tool_name TEXT,
    payload TEXT,
    outcome TEXT,
    error TEXT
);
"""


def db_path() -> Path:
    ensure_dirs()
    return STORE / "convoke.sqlite"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> Path:
    with connect() as conn:
        conn.executescript(SCHEMA)
    return db_path()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def fetchall(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def fetchone(query: str, params: tuple = ()) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def execute(query: str, params: tuple = ()) -> int:
    with connect() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid


def log_action(
    event_id: str | None,
    cycle_id: int | None,
    kind: str,
    tool_name: str | None = None,
    payload: Any = None,
    outcome: str | None = None,
    error: str | None = None,
) -> None:
    execute(
        """
        INSERT INTO action_log (event_id, cycle_id, timestamp, kind, tool_name, payload, outcome, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            cycle_id,
            utcnow(),
            kind,
            tool_name,
            json.dumps(payload, default=str) if payload is not None else None,
            outcome,
            error,
        ),
    )


def set_working_state(event_id: str, cycle_id: int, goal: str, plan: dict, pending: str | None) -> None:
    execute(
        """
        INSERT INTO working_state (event_id, cycle_id, current_goal, plan_json, pending_question, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(event_id) DO UPDATE SET
            cycle_id=excluded.cycle_id,
            current_goal=excluded.current_goal,
            plan_json=excluded.plan_json,
            pending_question=excluded.pending_question,
            updated_at=excluded.updated_at
        """,
        (event_id, cycle_id, goal, json.dumps(plan), pending, utcnow()),
    )
