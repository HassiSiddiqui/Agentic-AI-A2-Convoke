# Convoke

**A14 Academic event coordinator** for FAST-NUCES Agentic AI Assignment 2.

Student: **23i-2654 Abdul Haseeb Siddiqui**

Convoke is a single-agent hall porter. It onboards an academic event once, seats people against approved capacities, waitlists overflow, follows cancellations, and keeps an Excel register. SQLite is the authoritative memory. Notices stay **UNSENT** local drafts unless you approve a send and type SMTP details in the app.

This is not a chatbot. The model chooses the next follow-up. Python counts seats, validates dates, blocks duplicate notices, and writes the store.

## When you need the internet

| Feature | Internet? |
| --- | --- |
| Streamlit UI, SQLite, seat math, Excel, local drafts | **No** |
| Groq LLM decisions (`llama-3.3-70b-versatile`) | **Yes** (free tier). Offline, a deterministic fallback planner still runs. |
| Optional SMTP send | **Yes**, and only after you tick approval |
| Google Fonts in the UI | **Yes** for Syne/Fraunces. Offline, the browser falls back to Georgia / system UI |

You do **not** need the internet to demonstrate restart, isolation, correction, waitlists, or Excel export.

## Setup

Python 3.11+ recommended.

```powershell
cd c:\Uni\agenticai\A2_i232654_HaseebSiddiqui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Put a Groq API key in `.env` if you have one:

```
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
```

Leave SMTP blank unless you want live mail.

## Run the interface

```powershell
streamlit run app.py
```

1. Sidebar → **Load sample halls** (or Onboard → Seed both sample events).
2. **Review cycle** 1 with `data/samples/registrations_cycle1.csv`.
3. Fully close the terminal (process restart).
4. Start Streamlit again. Open Day is still in SQLite. Run cycle 2, then cycle 3.
5. **Approvals**: confirm seats; shrink Agent Clinic from 4 to 3.
6. **Ledger**: inspect history, action log, isolation probe (`EVT-POSTER`).
7. **Setup**: paste Groq / optional Gmail app password. Passwords stay in the browser session and are not written to SQLite.

## CLI

```powershell
python -m convoke seed
python -m convoke cycle --event EVT-OPENDAY --cycle 1 --file data\samples\registrations_cycle1.csv
python -m convoke evaluate
```

`--no-memory` disables long-term retrieval for the diagnostic comparison.

## Minimum demonstration (A14)

- Two sessions: Prompting Studio (`SESS-A`, cap 4) and Agent Clinic (`SESS-B`, cap 4).
- Eight first-cycle attendees; later a ninth with a planted instruction and a tenth with a missing preference; after restart an eleventh late registration.
- Cycle 1: capacity conflict on `SESS-A` (five requests, four seats, waitlist).
- Cycle 2: cancellation of P02; session switch; untrusted instruction; missing preference.
- Full process restart, then cycle 3 without re-uploading the original eight-row file.
- Approved capacity change 4 → 3 on `SESS-B`; history keeps 4.
- Isolated second event `EVT-POSTER`.

## Tools (meaningful, not wrappers)

1. **registration_reader** — local CSV/PDF/JSON ingest, SHA-256 duplicate skip, injection sanitise.
2. **policy_search** — retrieval over the approved local policy file.
3. **capacity_calculator** — deterministic remaining seats and waitlist promotion.
4. **record_allocations** — persistent SQLite write, unique `(event, cycle, participant)`.
5. **notice_writer** — UNSENT drafts; optional SMTP after approval + allowlist.
6. **excel_register** — review view that preserves organizer decision columns.
7. **update_session_fact** — organizer-approved correction with history.

## Repository / ZIP layout

```
app.py
convoke/          agent, tools, store, evaluate
assets/hall.css
data/samples/     anonymised inputs
data/store/       SQLite created on first run
docs/             report, proposal text, memory schema, demo script
outputs/          Excel register and notice drafts
reports/          scenario results after evaluate
.env.example
requirements.txt
```

Classroom ZIP (no secrets, no class workbook): `A2_23i-2654_AbdulHaseebSiddiqui_Convoke.zip`. Rebuild with `python scripts\pack_submission.py` after you re-run evaluate.

Do not commit `.env` or Gmail passwords.

## GitHub

See `docs/GITHUB.md`. You need a GitHub account, Git installed, and a new empty repository. I will not push until you send the repo URL and confirm the remote.

## Disclosure

AI assistance was used to implement Convoke. The student must be able to explain memory, tools, and the decision loop in the viva. All demo people and emails are fictional (`example.com`).
