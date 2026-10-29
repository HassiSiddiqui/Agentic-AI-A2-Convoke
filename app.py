from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from convoke.agent import run_cycle
from convoke.config import Settings, settings_from_overrides
from convoke.labels import PAGES, action_label, status_label
from convoke.onboard import approve_allocation, onboard_event
from convoke.paths import ROOT, SAMPLES, UPLOADS, ensure_dirs
from convoke.seed import seed_demo
from convoke.store import fetchall, fetchone, init_db, log_action
from convoke.tools import tool_excel_register, tool_update_session_fact

st.set_page_config(page_title="Convoke · Event coordinator", page_icon="🎟️", layout="wide")
ensure_dirs()
init_db()
st.markdown(f"<style>{(ROOT / 'assets' / 'hall.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

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


def pretty_placements(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    frame["status"] = frame["agent_status"].map(status_label)
    frame["follow_up"] = frame["next_action"].map(action_label)
    keep = [col for col in ["participant_id", "session_id", "status", "follow_up", "evidence", "blocker"] if col in frame.columns]
    return frame[keep]


with st.sidebar:
    st.markdown('<p class="kicker">Convoke</p>', unsafe_allow_html=True)
    st.markdown("### Event coordinator")
    st.caption("Allocate lab seats, keep a waitlist, and remember decisions after restart.")
    st.markdown('<p class="nav-label">Pages</p>', unsafe_allow_html=True)
    for name, hint in PAGES:
        clicked = st.button(
            name,
            key=f"nav-{name}",
            use_container_width=True,
            type="primary" if st.session_state.nav == name else "secondary",
            help=hint,
        )
        if clicked and st.session_state.nav != name:
            go(name)

    page = st.session_state.nav
    events = fetchall("SELECT event_id, title FROM events ORDER BY created_at")
    event_ids = [row["event_id"] for row in events] or ["EVT-OPENDAY"]
    event_id = st.selectbox("Current event", event_ids, help="Each event has its own memory.")
    cycle_id = st.number_input("Review cycle", min_value=1, max_value=12, value=1, step=1)
    st.divider()
    if st.button("Load demo events", use_container_width=True):
        seed_demo()
        st.rerun()
    st.caption("Loads Open Day and Poster Hour. Close the app and reopen to show restart.")


if page == "Home":
    event = fetchone("SELECT * FROM events WHERE event_id=?", (event_id,))
    sessions = fetchall("SELECT * FROM sessions WHERE event_id=? AND is_current=1", (event_id,))
    allocations = fetchall("SELECT * FROM allocations WHERE event_id=? AND is_current=1", (event_id,))
    wait = fetchall("SELECT * FROM waitlist WHERE event_id=? AND is_current=1", (event_id,))
    working = fetchone("SELECT * FROM working_state WHERE event_id=?", (event_id,))
    title = event["title"] if event else "No event loaded"
    confirmed = sum(1 for row in allocations if row["agent_status"] == "Evidence supports completion")
    next_step = (working or {}).get("current_goal") or "Create an event or load the demo"

    st.markdown(
        f"""
        <div class="hero">
          <div class="kicker">Assignment 2 · A14 · 23i-2654</div>
          <h1>Convoke</h1>
          <p>A working desk for academic sessions with limited seats. Upload registrations, confirm or waitlist people, and keep notices unsent until you approve email.</p>
          <div class="ticket-row">
            <div class="ticket"><span>Event</span><b title="{title}">{title}</b></div>
            <div class="ticket"><span>Sessions</span><b>{len(sessions)}</b></div>
            <div class="ticket"><span>Confirmed</span><b>{confirmed}</b></div>
            <div class="ticket"><span>Waitlist</span><b>{len(wait)}</b></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not event:
        st.info("Nothing is saved yet. Load the demo events, or create your own.")
        empty_a, empty_b = st.columns(2)
        with empty_a:
            if st.button("Load demo events", type="primary", use_container_width=True, key="home-demo"):
                seed_demo()
                st.rerun()
        with empty_b:
            if st.button("Create an event", use_container_width=True, key="home-create"):
                go("Create event")

    st.markdown("#### Workflow")
    a, b, c, d = st.columns(4)
    cards = [
        (a, "Create event", "Save two sessions and their capacities once.", "Create event"),
        (b, "Run review", "Read a registration file and allocate seats.", "Run review"),
        (c, "Confirm seats", "Record your decision without changing the agent status.", "Confirm seats"),
        (d, "Notices", "Keep drafts local, or send after you approve email.", "Notices"),
    ]
    for col, heading, text, target in cards:
        with col:
            st.markdown(
                f'<div class="action-card"><h4>{heading}</h4><p>{text}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(heading, use_container_width=True, key=f"jump-{target}"):
                go(target)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Language model (Groq)", "Needs internet")
    m2.metric("Send email", "Optional")
    m3.metric("Seats and Excel", "Works offline")
    m4.metric("Next step", next_step)

    st.markdown("#### Seat map")
    st.caption("Copper = confirmed · Gold = waitlist or review · Green = unused slot")
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
            f'<span class="badge gold">checkpoint</span> Cycle {working["cycle_id"]} · {working["current_goal"]}',
            unsafe_allow_html=True,
        )
        if working.get("pending_question"):
            st.warning(working["pending_question"])

    if sessions:
        st.markdown("#### Sessions")
        cards_html = '<div class="session-board">'
        for sess in sessions:
            cap = int(sess["capacity"] or 0)
            taken = sum(
                1
                for row in allocations
                if row["session_id"] == sess["session_id"]
                and row["agent_status"] == "Evidence supports completion"
            )
            pct = 0 if cap == 0 else min(100, int(100 * taken / cap))
            cards_html += (
                f'<div class="session-card"><div class="meta">{sess["session_id"]} · {sess["room"]} · '
                f'{sess["starts_at"]}–{sess["ends_at"]}</div><h4>{sess["name"]}</h4>'
                f"<p>{taken} of {cap} approved seats filled</p>"
                f'<div class="capacity-bar"><span style="width:{pct}%"></span></div></div>'
            )
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

    e1, e2 = st.columns(2)
    with e1:
        if st.button("Open records and logs", use_container_width=True):
            go("Records")
    with e2:
        if st.button("Open settings", use_container_width=True):
            go("Settings")


elif page == "Create event":
    page_heading(
        "Step 1 of 4",
        "Create event",
        "Approve the baseline once. Later cycles reload it from SQLite, so you do not upload this form again.",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        eid = st.text_input("Event ID", value="EVT-OPENDAY")
        title = st.text_input("Title", value="FAST-NUCES Agentic Systems Open Day")
        venue = st.text_input("Venue", value="CS Atrium")
        date = st.text_input("Date", value="2026-11-12")
    with col_b:
        st.markdown("**Session A**")
        a_id = st.text_input("ID", value="SESS-A", key="a_id")
        a_name = st.text_input("Name", value="Prompting Studio", key="a_name")
        a_room = st.text_input("Room", value="Lab 4", key="a_room")
        a_start, a_end, a_cap = st.columns(3)
        with a_start:
            a_starts = st.text_input("Starts", value="10:00")
        with a_end:
            a_ends = st.text_input("Ends", value="11:20")
        with a_cap:
            a_capacity = st.number_input("Seats", min_value=1, max_value=80, value=4, key="a_cap")

    st.markdown("**Session B**")
    b1, b2, b3 = st.columns(3)
    with b1:
        b_id = st.text_input("ID", value="SESS-B", key="b_id")
        b_name = st.text_input("Name", value="Agent Clinic", key="b_name")
    with b2:
        b_room = st.text_input("Room", value="Lab 5", key="b_room")
        b_starts = st.text_input("Starts", value="10:00", key="b_starts")
    with b3:
        b_ends = st.text_input("Ends", value="11:20", key="b_ends")
        b_capacity = st.number_input("Seats", min_value=1, max_value=80, value=4, key="b_cap")

    save, demo = st.columns(2)
    with save:
        if st.button("Save event", type="primary", use_container_width=True):
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
                st.success(f"Saved {eid}. Continue with Run review.")
            else:
                st.info(f"{eid} already exists. Choose a new ID, or continue with Run review.")
    with demo:
        if st.button("Load demo instead", use_container_width=True):
            seed_demo()
            st.success("Loaded Open Day and Poster Hour. Open Run review.")
            st.rerun()


elif page == "Run review":
    page_heading(
        "Step 2 of 4",
        "Run review",
        "Python counts seats. The model only chooses the follow-up. Close Streamlit between cycles to demonstrate restart.",
    )
    default_files = {
        1: str(SAMPLES / "registrations_cycle1.csv"),
        2: str(SAMPLES / "updates_cycle2.csv"),
        3: str(SAMPLES / "updates_cycle3.csv"),
    }
    path = st.text_input(
        "Registration file",
        value=default_files.get(int(cycle_id), str(SAMPLES / "registrations_cycle1.csv")),
        help="Cycle 1: eight people. Cycle 2: cancellation and a missing preference. Cycle 3: late registration after restart.",
    )
    uploaded = st.file_uploader("Or drop a CSV, TXT, JSON, or PDF", type=["csv", "txt", "pdf", "json"])
    if uploaded:
        dest = UPLOADS / uploaded.name
        dest.write_bytes(uploaded.getvalue())
        path = str(dest)
        st.caption(f"Using {dest.name}")

    opt1, opt2 = st.columns(2)
    with opt1:
        memory_on = st.toggle("Use saved memory", value=True, help="Turn off only for the memory-off comparison.")
        send = st.toggle("Send email this cycle", value=False, help="Requires approval on Notices and SMTP in Settings.")
    with opt2:
        fail_write = st.toggle("Simulate save failure", value=False)
        fail_mail = st.toggle("Simulate email failure", value=False)

    if st.button("Run this cycle", type="primary"):
        settings = current_settings()
        with st.spinner("Reading the file and counting remaining seats…"):
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
            f'<span class="badge {badge}">{action_label(plan.get("next_action"))}</span> '
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
        st.dataframe(pretty_placements(result["capacity"]["placements"]), hide_index=True, use_container_width=True)
        if result["flagged_injections"]:
            st.error("The file contained an instruction-like note. Capacity, recipients, and permissions were not changed.")
        if not result["recorded"].get("ok"):
            st.error(result["recorded"])
        else:
            st.success(f"Excel register updated: {result['register_path']}")
            n1, n2 = st.columns(2)
            with n1:
                if st.button("Go to Confirm seats", type="primary"):
                    go("Confirm seats")
            with n2:
                if st.button("Go to Notices"):
                    go("Notices")


elif page == "Confirm seats":
    page_heading(
        "Step 3 of 4",
        "Confirm seats",
        "Your decision is stored separately from the agent suggestion. Excel keeps your comments on re-export.",
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
        st.info("No placements for this cycle. Run a review first.")
        if st.button("Go to Run review", type="primary"):
            go("Run review")
    for row in rows:
        with st.expander(f"{row['display_name']} · {status_label(row['agent_status'])}"):
            st.write(f"Evidence: {row['evidence']}")
            st.write(f"Blocker: {row['blocker'] or 'None'}")
            st.write(f"Suggested follow-up: {action_label(row['next_action'])}")
            decision = st.selectbox(
                "Your decision",
                ["", "Confirmed", "Rejected", "Needs review", "Waitlisted"],
                key=f"d-{row['allocation_id']}",
            )
            comment = st.text_input("Comment (optional)", key=f"c-{row['allocation_id']}")
            if st.button("Save decision", key=f"s-{row['allocation_id']}"):
                approve_allocation(event_id, int(cycle_id), row["participant_id"], decision, comment)
                st.success("Saved. The agent status is unchanged.")

    st.markdown("---")
    st.markdown("#### Change an approved fact")
    st.caption("Example: reduce capacity after a room problem. The previous number stays in history.")
    sessions = fetchall("SELECT session_id, name, capacity FROM sessions WHERE event_id=? AND is_current=1", (event_id,))
    if sessions:
        labels = {s["session_id"]: f"{s['name']} ({s['session_id']}, {s['capacity']} seats)" for s in sessions}
        sid = st.selectbox("Session", list(labels), format_func=lambda x: labels.get(x, x))
        new_cap = st.number_input("New capacity", min_value=1, max_value=40, value=3)
        reason = st.text_input("Reason", value="Projector failed; reduce Agent Clinic")
        if st.button("Save capacity change"):
            result = tool_update_session_fact(event_id, sid, "capacity", str(int(new_cap)), "organizer", reason)
            st.success(f"Capacity {result.get('old')} → {result.get('new')}. The next review uses the new value.")


elif page == "Notices":
    page_heading(
        "Step 4 of 4",
        "Notices",
        "Drafts stay on disk as UNSENT until you approve sending and add SMTP details in Settings.",
    )
    notices = fetchall("SELECT * FROM notices WHERE event_id=? ORDER BY notice_id DESC", (event_id,))
    if notices:
        view = pd.DataFrame(notices)
        keep = [c for c in ["notice_id", "participant_id", "cycle_id", "subject", "recipient", "status", "delivery_outcome", "approved"] if c in view.columns]
        st.dataframe(view[keep], hide_index=True, use_container_width=True)
    else:
        st.info("No drafts yet. Run a review cycle first.")
        if st.button("Go to Run review"):
            go("Run review")
    st.session_state.send_approved = st.checkbox(
        "I approve sending the next batch, but only to addresses on the allowlist",
        value=st.session_state.send_approved,
    )
    st.caption("SMTP passwords typed in Settings stay in this browser session. They are not written to SQLite.")
    if st.button("Open email settings"):
        go("Settings")


elif page == "Records":
    page_heading(
        "Memory",
        "Records",
        "SQLite is authoritative. Excel is a review copy and does not overwrite your decisions.",
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
        other = st.text_input("Other event ID", value="EVT-POSTER")
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
        "This machine only",
        "Settings",
        "Keys stay local. Groq is free-tier. Email is optional.",
    )
    default = Settings()
    st.markdown("#### Groq")
    st.session_state.groq_key = st.text_input("API key", type="password", value=default.groq_api_key)
    st.session_state.groq_model = st.text_input("Model", value=default.groq_model)
    st.caption("Needs internet. If the key is empty, Convoke still allocates seats with the offline planner.")
    st.markdown("#### Optional email")
    st.session_state.smtp_host = st.text_input("SMTP host", value=default.smtp_host)
    st.session_state.smtp_port = st.number_input("SMTP port", value=default.smtp_port)
    st.session_state.smtp_user = st.text_input("Username / Gmail", value=default.smtp_username)
    st.session_state.smtp_password = st.text_input("Password or Gmail app password", type="password")
    st.session_state.smtp_from = st.text_input("From address", value=default.smtp_from)
    st.session_state.smtp_allow = st.text_input("Allowed recipients (comma-separated)", value=default.smtp_allowlist)
    st.markdown(
        """
**When you need the internet**

- Groq: yes, unless you use the offline planner.
- Sending email: yes, and only after you tick approval on Notices.
- Creating events, counting seats, SQLite, Excel, local drafts: no.
        """
    )
    log_action(event_id, None, "ui", payload={"page": "settings"}, outcome="viewed")
