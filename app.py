from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from convoke.agent import run_cycle
from convoke.config import Settings, settings_from_overrides
from convoke.onboard import approve_allocation, onboard_event
from convoke.paths import ROOT, SAMPLES, UPLOADS, ensure_dirs
from convoke.seed import seed_demo
from convoke.store import fetchall, fetchone, init_db, log_action
from convoke.tools import tool_excel_register, tool_update_session_fact

PAGES = [
    "Home",
    "Create event",
    "Run review",
    "Confirm seats",
    "Notices",
    "Records",
    "Settings",
]

st.set_page_config(page_title="Convoke · Event coordinator", page_icon="🎟️", layout="wide")
ensure_dirs()
init_db()
css = (ROOT / "assets" / "hall.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

if "smtp_password" not in st.session_state:
    st.session_state.smtp_password = ""
if "send_approved" not in st.session_state:
    st.session_state.send_approved = False
if "nav" not in st.session_state:
    st.session_state.nav = "Home"


def go(page: str) -> None:
    st.session_state.nav = page
    st.rerun()


def current_settings() -> Settings:
    return settings_from_overrides(
        groq_api_key=st.session_state.get("groq_key") or None,
        groq_model=st.session_state.get("groq_model") or None,
        smtp_host=st.session_state.get("smtp_host") or None,
        smtp_port=int(st.session_state.get("smtp_port") or 587),
        smtp_username=st.session_state.get("smtp_user") or None,
        smtp_password=st.session_state.smtp_password or None,
        smtp_from=st.session_state.get("smtp_from") or None,
        smtp_allowlist=st.session_state.get("smtp_allow") or None,
    )


def page_heading(kicker: str, title: str, blurb: str) -> None:
    st.markdown(
        f"""
        <div class="page-head">
          <p class="kicker">{kicker}</p>
          <h2>{title}</h2>
          <p class="blurb">{blurb}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown('<p class="kicker">Convoke</p>', unsafe_allow_html=True)
    st.markdown("### Academic events")
    st.caption("Seat people, keep a waitlist, and remember decisions after restart.")
    page = st.radio("Go to", PAGES, key="nav")
    events = fetchall("SELECT event_id, title FROM events ORDER BY created_at")
    event_ids = [row["event_id"] for row in events] or ["EVT-OPENDAY"]
    event_id = st.selectbox("Working event", event_ids)
    cycle_id = st.number_input("Review cycle", min_value=1, max_value=12, value=1, step=1)
    st.divider()
    if st.button("Load demo events", use_container_width=True):
        seed_demo()
        st.rerun()
    st.caption("Demo loads Open Day and an isolated poster event. Saved state is in SQLite and survives closing the app.")


if page == "Home":
    event = fetchone("SELECT * FROM events WHERE event_id=?", (event_id,))
    sessions = fetchall("SELECT * FROM sessions WHERE event_id=? AND is_current=1", (event_id,))
    allocations = fetchall("SELECT * FROM allocations WHERE event_id=? AND is_current=1", (event_id,))
    wait = fetchall("SELECT * FROM waitlist WHERE event_id=? AND is_current=1", (event_id,))
    working = fetchone("SELECT * FROM working_state WHERE event_id=?", (event_id,))
    title = event["title"] if event else "No event yet — create one or load the demo"
    confirmed = sum(1 for row in allocations if row["agent_status"] == "Evidence supports completion")

    st.markdown(
        f"""
        <div class="hero">
          <div class="kicker">A14 academic event coordinator · 23i-2654</div>
          <h1>Convoke</h1>
          <p>Allocate limited lab sessions, waitlist overflow, and follow cancellations. The agent remembers approved capacities and earlier decisions after you restart the app.</p>
          <div class="ticket-row">
            <div class="ticket"><span>Event</span><b>{title}</b></div>
            <div class="ticket"><span>Sessions</span><b>{len(sessions)}</b></div>
            <div class="ticket"><span>Confirmed seats</span><b>{confirmed}</b></div>
            <div class="ticket"><span>Waitlist</span><b>{len(wait)}</b></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Start here")
    a, b, c, d = st.columns(4)
    with a:
        st.markdown('<div class="action-card"><h4>1. Create event</h4><p>Save the two sessions and capacities once.</p></div>', unsafe_allow_html=True)
        if st.button("Open create event", use_container_width=True):
            go("Create event")
    with b:
        st.markdown('<div class="action-card"><h4>2. Run review</h4><p>Ingest a registration file and seat people.</p></div>', unsafe_allow_html=True)
        if st.button("Open run review", use_container_width=True):
            go("Run review")
    with c:
        st.markdown('<div class="action-card"><h4>3. Confirm seats</h4><p>Keep your decision separate from the agent.</p></div>', unsafe_allow_html=True)
        if st.button("Open confirm seats", use_container_width=True):
            go("Confirm seats")
    with d:
        st.markdown('<div class="action-card"><h4>4. Notices</h4><p>Drafts stay unsent unless you approve email.</p></div>', unsafe_allow_html=True)
        if st.button("Open notices", use_container_width=True):
            go("Notices")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Groq (LLM)", "Needs internet")
    m2.metric("Send email", "Optional, needs internet")
    m3.metric("Seats, SQLite, Excel", "Works offline")
    m4.metric("Recommended next step", (working or {}).get("current_goal") or "Create or load an event")

    st.markdown("#### Seat map")
    st.caption("Copper = confirmed · Gold = waitlist or review · Green = open")
    seats_html = '<div class="seat-grid">'
    for row in allocations[:24]:
        klass = "taken" if row["agent_status"] == "Evidence supports completion" else "wait"
        seats_html += f'<div class="seat {klass}" title="{row["participant_id"]}"></div>'
    for _ in range(max(0, 16 - len(allocations))):
        seats_html += '<div class="seat free"></div>'
    seats_html += "</div>"
    st.markdown(seats_html, unsafe_allow_html=True)

    if working:
        st.markdown(
            f'<span class="badge gold">saved checkpoint</span> Cycle {working["cycle_id"]} · {working["current_goal"]}',
            unsafe_allow_html=True,
        )
        if working.get("pending_question"):
            st.warning(working["pending_question"])

    if sessions:
        st.markdown("#### Sessions")
        cards = '<div class="session-board">'
        for sess in sessions:
            cap = int(sess["capacity"] or 0)
            taken = sum(
                1
                for row in allocations
                if row["session_id"] == sess["session_id"]
                and row["agent_status"] == "Evidence supports completion"
            )
            pct = 0 if cap == 0 else min(100, int(100 * taken / cap))
            cards += (
                f'<div class="session-card"><div class="meta">{sess["session_id"]} · {sess["room"]} · '
                f'{sess["starts_at"]}–{sess["ends_at"]}</div><h4>{sess["name"]}</h4>'
                f'<p>{taken} confirmed of {cap} approved seats</p>'
                f'<div class="capacity-bar"><span style="width:{pct}%"></span></div></div>'
            )
        cards += "</div>"
        st.markdown(cards, unsafe_allow_html=True)

    e1, e2 = st.columns(2)
    with e1:
        if st.button("View records and logs", use_container_width=True):
            go("Records")
    with e2:
        if st.button("API keys and email", use_container_width=True):
            go("Settings")


elif page == "Create event":
    page_heading(
        "Step 1",
        "Create event",
        "Approve the baseline once. Later reviews reload it from SQLite, so you do not upload this again.",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        eid = st.text_input("Event ID", value="EVT-OPENDAY")
        title = st.text_input("Title", value="FAST-NUCES Agentic Systems Open Day")
        venue = st.text_input("Venue", value="CS Atrium")
        date = st.text_input("Date", value="2026-11-12")
    with col_b:
        st.markdown("**Session A**")
        a_id = st.text_input("Session A ID", value="SESS-A")
        a_name = st.text_input("Session A name", value="Prompting Studio")
        a_room = st.text_input("Session A room", value="Lab 4")
        a_start, a_end, a_cap = st.columns(3)
        with a_start:
            a_starts = st.text_input("Starts", value="10:00")
        with a_end:
            a_ends = st.text_input("Ends", value="11:20")
        with a_cap:
            a_capacity = st.number_input("Capacity", min_value=1, max_value=80, value=4, key="a_cap")
    st.markdown("**Session B**")
    b1, b2, b3 = st.columns(3)
    with b1:
        b_id = st.text_input("Session B ID", value="SESS-B")
        b_name = st.text_input("Session B name", value="Agent Clinic")
    with b2:
        b_room = st.text_input("Session B room", value="Lab 5")
        b_starts = st.text_input("Session B starts", value="10:00")
    with b3:
        b_ends = st.text_input("Session B ends", value="11:20")
        b_capacity = st.number_input("Session B capacity", min_value=1, max_value=80, value=4, key="b_cap")

    save, demo = st.columns(2)
    with save:
        if st.button("Save approved baseline", type="primary", use_container_width=True):
            result = onboard_event(
                eid,
                "org-haseeb",
                title,
                venue,
                date,
                [
                    {
                        "session_id": a_id,
                        "name": a_name,
                        "room": a_room,
                        "starts_at": a_starts,
                        "ends_at": a_ends,
                        "capacity": int(a_capacity),
                    },
                    {
                        "session_id": b_id,
                        "name": b_name,
                        "room": b_room,
                        "starts_at": b_starts,
                        "ends_at": b_ends,
                        "capacity": int(b_capacity),
                    },
                ],
            )
            if result.get("created"):
                st.success(f"Saved {eid}. Next: Run review.")
            else:
                st.info(f"{eid} already exists. Use a new ID or continue to Run review.")
    with demo:
        if st.button("Load both demo events instead", use_container_width=True):
            st.json(seed_demo())
            st.success("Loaded EVT-OPENDAY and EVT-POSTER. Open Run review next.")


elif page == "Run review":
    page_heading(
        "Step 2",
        "Run review",
        "The model chooses the next follow-up. Python counts seats and writes SQLite. Close the app between cycles to show restart.",
    )
    default_files = {
        1: str(SAMPLES / "registrations_cycle1.csv"),
        2: str(SAMPLES / "updates_cycle2.csv"),
        3: str(SAMPLES / "updates_cycle3.csv"),
    }
    path = st.text_input(
        "Registration file path",
        value=default_files.get(int(cycle_id), str(SAMPLES / "registrations_cycle1.csv")),
        help="Cycle 1 = eight attendees. Cycle 2 = cancellation and missing preference. Cycle 3 = late registration after restart.",
    )
    uploaded = st.file_uploader("Or upload CSV, TXT, JSON, or PDF", type=["csv", "txt", "pdf", "json"])
    if uploaded:
        dest = UPLOADS / uploaded.name
        dest.write_bytes(uploaded.getvalue())
        path = str(dest)
        st.caption(f"Using uploaded file {dest.name}")

    opt1, opt2 = st.columns(2)
    with opt1:
        memory_on = st.toggle("Use saved memory", value=True, help="Turn off only for the memory-off diagnostic comparison.")
        send = st.toggle("Send notices by email", value=False, help="Also tick send approval on the Notices page and add SMTP in Settings.")
    with opt2:
        fail_write = st.toggle("Simulate save failure", value=False)
        fail_mail = st.toggle("Simulate email failure", value=False)

    if st.button("Run this cycle", type="primary"):
        settings = current_settings()
        with st.spinner("Reviewing registrations and remaining seats…"):
            result = run_cycle(
                settings=settings,
                event_id=event_id,
                cycle_id=int(cycle_id),
                source_paths=[path] if path else [],
                memory_enabled=memory_on,
                send_notices=send,
                approved_send=st.session_state.send_approved and send,
                simulate_write_failure=fail_write,
                simulate_smtp_failure=fail_mail,
            )
        st.session_state["last_result"] = result
        plan = result["plan"]
        badge = "warn" if plan.get("uncertain") else "ok"
        mode = "offline planner" if plan.get("fallback") else plan.get("model", "groq")
        st.markdown(
            f'<span class="badge {badge}">{plan.get("next_action")}</span> '
            f'<span class="badge idle">{mode}</span>',
            unsafe_allow_html=True,
        )
        st.write(plan.get("analysis"))
        if plan.get("pending_question"):
            st.info(plan["pending_question"])
        left, right = st.columns(2)
        with left:
            st.markdown("**Remaining seats**")
            st.json(result["capacity"]["remaining"])
        with right:
            st.markdown("**Tools used**")
            st.write(", ".join(result.get("tools_run") or []))
        st.markdown("**Placements**")
        st.dataframe(pd.DataFrame(result["capacity"]["placements"]), hide_index=True, use_container_width=True)
        if result["flagged_injections"]:
            st.error("A source file contained an instruction-like note. Capacity, recipients, and permissions were not changed.")
        if not result["recorded"].get("ok"):
            st.error(result["recorded"])
        else:
            st.success(f"Excel register updated: {result['register_path']}")
            n1, n2 = st.columns(2)
            with n1:
                if st.button("Confirm these seats"):
                    go("Confirm seats")
            with n2:
                if st.button("Open notices"):
                    go("Notices")


elif page == "Confirm seats":
    page_heading(
        "Step 3",
        "Confirm seats",
        "Your decision is stored separately from the agent suggestion. Excel exports keep your comments.",
    )
    rows = fetchall(
        """
        SELECT a.*, p.display_name FROM allocations a
        JOIN participants p ON p.participant_id=a.participant_id AND p.event_id=a.event_id
        WHERE a.event_id=? AND a.cycle_id=?
        """,
        (event_id, int(cycle_id)),
    )
    if not rows:
        st.info("No allocations for this cycle yet. Open Run review first.")
        if st.button("Go to Run review"):
            go("Run review")
    for row in rows:
        with st.expander(f"{row['display_name']} · agent: {row['agent_status']}"):
            st.write(f"Evidence: {row['evidence']}")
            st.write(f"Blocker: {row['blocker'] or 'None'}")
            st.write(f"Recommended next action: {row['next_action']}")
            decision = st.selectbox(
                "Your decision",
                ["", "Confirmed", "Rejected", "Needs review", "Waitlisted"],
                key=f"d-{row['allocation_id']}",
            )
            comment = st.text_input("Comment (optional)", key=f"c-{row['allocation_id']}")
            if st.button("Save your decision", key=f"s-{row['allocation_id']}"):
                approve_allocation(event_id, int(cycle_id), row["participant_id"], decision, comment)
                st.success("Saved. This does not overwrite the agent status.")

    st.markdown("---")
    st.markdown("#### Change an approved fact")
    st.caption("Example: shrink a room after a projector failure. The old capacity stays in history.")
    sessions = fetchall("SELECT session_id, name, capacity FROM sessions WHERE event_id=? AND is_current=1", (event_id,))
    if sessions:
        labels = {s["session_id"]: f"{s['name']} ({s['session_id']}, capacity {s['capacity']})" for s in sessions}
        sid = st.selectbox("Session", list(labels), format_func=lambda x: labels.get(x, x))
        new_cap = st.number_input("New capacity", min_value=1, max_value=40, value=3)
        reason = st.text_input("Reason", value="Room projector failed; reduce Agent Clinic")
        if st.button("Approve capacity change"):
            result = tool_update_session_fact(event_id, sid, "capacity", str(int(new_cap)), "organizer", reason)
            st.success(f"Capacity {result.get('old')} → {result.get('new')}. Later reviews use the new value.")


elif page == "Notices":
    page_heading(
        "Step 4",
        "Notices",
        "Every notice is an UNSENT local draft until you approve sending and add SMTP details in Settings.",
    )
    notices = fetchall("SELECT * FROM notices WHERE event_id=? ORDER BY notice_id DESC", (event_id,))
    if notices:
        st.dataframe(pd.DataFrame(notices), hide_index=True, use_container_width=True)
    else:
        st.info("No drafts yet. Run a review cycle first.")
    st.session_state.send_approved = st.checkbox(
        "I approve sending the next batch to allowlisted addresses only",
        value=st.session_state.send_approved,
    )
    st.caption("Passwords typed in Settings stay in this browser session. They are not saved in SQLite.")
    if st.button("Open email settings"):
        go("Settings")


elif page == "Records":
    page_heading(
        "Memory",
        "Records",
        "SQLite is the source of truth. Excel is a review copy and will not overwrite your decisions.",
    )
    tabs = st.tabs(["Allocations", "Capacity history", "Action log", "Event isolation"])
    with tabs[0]:
        data = fetchall("SELECT * FROM allocations WHERE event_id=? ORDER BY cycle_id, allocation_id", (event_id,))
        st.dataframe(pd.DataFrame(data) if data else pd.DataFrame(), hide_index=True, use_container_width=True)
    with tabs[1]:
        hist = fetchall("SELECT * FROM session_history WHERE event_id=? ORDER BY changed_at DESC", (event_id,))
        st.dataframe(pd.DataFrame(hist) if hist else pd.DataFrame(), hide_index=True, use_container_width=True)
    with tabs[2]:
        logs = fetchall("SELECT * FROM action_log ORDER BY log_id DESC LIMIT 200")
        st.dataframe(pd.DataFrame(logs) if logs else pd.DataFrame(), hide_index=True, use_container_width=True)
    with tabs[3]:
        other = st.text_input("Compare against another event ID", value="EVT-POSTER")
        leaked = fetchall("SELECT participant_id, display_name, event_id FROM participants WHERE event_id=?", (other,))
        mine = fetchall("SELECT participant_id, display_name, event_id FROM participants WHERE event_id=?", (event_id,))
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{event_id}**")
            st.dataframe(pd.DataFrame(mine) if mine else pd.DataFrame(), hide_index=True, use_container_width=True)
        with c2:
            st.markdown(f"**{other}**")
            st.dataframe(pd.DataFrame(leaked) if leaked else pd.DataFrame(), hide_index=True, use_container_width=True)
        if event_id != other:
            overlap = {row["participant_id"] for row in mine} & {row["participant_id"] for row in leaked}
            if overlap:
                st.error("Isolation failed: the same participant id appeared in both events.")
            else:
                st.success("Isolation holds: this query does not mix the two events.")
    if st.button("Export Excel register"):
        path = tool_excel_register(event_id)
        st.success(path)
        st.download_button("Download Excel", data=Path(path).read_bytes(), file_name=Path(path).name)


elif page == "Settings":
    page_heading(
        "Local only",
        "Settings",
        "Keys stay on this machine. Groq is free-tier. Email is optional.",
    )
    default = Settings()
    st.markdown("#### Groq")
    st.session_state.groq_key = st.text_input("Groq API key", type="password", value=default.groq_api_key)
    st.session_state.groq_model = st.text_input("Model", value=default.groq_model)
    st.caption("Needs internet. If the key is empty, Convoke still seats people with the offline planner.")
    st.markdown("#### Optional email")
    st.session_state.smtp_host = st.text_input("SMTP host", value=default.smtp_host)
    st.session_state.smtp_port = st.number_input("SMTP port", value=default.smtp_port)
    st.session_state.smtp_user = st.text_input("SMTP username / Gmail", value=default.smtp_username)
    st.session_state.smtp_password = st.text_input("SMTP password or Gmail app password", type="password")
    st.session_state.smtp_from = st.text_input("From address", value=default.smtp_from)
    st.session_state.smtp_allow = st.text_input("Allowed recipients (comma-separated)", value=default.smtp_allowlist)
    st.markdown(
        """
**Internet**
- Groq decisions: required for the LLM, optional if you accept the offline planner.
- Sending email: required, and only after you approve on Notices.
- Creating events, counting seats, SQLite, Excel, local drafts: work offline.

Do not put keys in CSV files or commit `.env`.
        """
    )
    log_action(event_id, None, "ui", payload={"page": "settings"}, outcome="viewed")
