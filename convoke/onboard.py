from __future__ import annotations

from convoke.audit import utcnow
from convoke.store import execute, fetchone, log_action, set_working_state


def onboard_event(
    event_id: str,
    organizer_id: str,
    title: str,
    venue: str,
    event_date: str,
    sessions: list[dict],
    notes: str = "",
) -> dict:
    existing = fetchone("SELECT event_id FROM events WHERE event_id=?", (event_id,))
    if existing:
        log_action(event_id, 0, "onboard", payload={"duplicate": True}, outcome="already_exists")
        return {"ok": True, "created": False, "event_id": event_id}

    execute(
        """
        INSERT INTO events (event_id, organizer_id, title, venue, event_date, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, organizer_id, title, venue, event_date, notes, utcnow()),
    )
    for session in sessions:
        execute(
            """
            INSERT INTO sessions (session_id, event_id, name, room, starts_at, ends_at, capacity, version, is_current)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
            """,
            (
                session["session_id"],
                event_id,
                session["name"],
                session.get("room"),
                session.get("starts_at"),
                session.get("ends_at"),
                int(session["capacity"]),
            ),
        )
    set_working_state(event_id, 0, "Onboarded. Awaiting first registration cycle.", {"next": "ingest"}, None)
    log_action(event_id, 0, "onboard", payload={"sessions": len(sessions)}, outcome="created")
    return {"ok": True, "created": True, "event_id": event_id}


def approve_allocation(event_id: str, cycle_id: int, participant_id: str, decision: str, comment: str) -> None:
    execute(
        """
        UPDATE allocations
        SET organizer_status=?, organizer_comment=?
        WHERE event_id=? AND cycle_id=? AND participant_id=?
        """,
        (decision, comment, event_id, cycle_id, participant_id),
    )
    log_action(event_id, cycle_id, "approval", payload={"participant_id": participant_id, "decision": decision}, outcome="saved")
