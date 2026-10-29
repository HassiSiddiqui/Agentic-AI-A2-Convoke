# Paste this into Proposal approval-DS-A (your own empty row only)

Leave **Teacher decision** and **Teacher comments** blank.

## Student ID/Rollnumber

23i-2654

## Student name

Abdul Haseeb Siddiqui

## Idea ID or own title

A14 – Academic event coordinator (Convoke)

## User and minimum workflow

User: an academic organizer (course society / open-day porter) who repeatedly allocates limited lab sessions as registrations, cancellations and capacity changes arrive.

Workflow: (1) Onboard an event once: title, venue, date, and two sessions with approved capacities; I confirm this baseline. (2) Each review cycle, ingest a registration or update file (CSV/PDF). The agent retrieves approved capacities, current seats, waitlist, prior notices and unresolved questions. Python counts remaining seats. The LLM chooses the next action from evidence: confirm a seat, waitlist overflow, promote the waitlist after a cancellation, ask for a missing preference, or wait. (3) It writes a per-cycle allocation register, shows the recommended next action with evidence, and drafts notices labelled UNSENT. Sending to an allowlisted address happens only if I tick approval and provide SMTP details in the app; otherwise drafts stay local.

Demo: 2 sessions, 8 attendees in cycle 1, 3 cycles, one capacity conflict, one cancellation, one approved capacity change (4→3), one report/file update after restart, and an isolated second event.

## Memory and restart demonstration

SQLite (`data/store/convoke.sqlite`) is the authoritative store, keyed by event_id, session_id, participant_id and cycle_id. It remembers: approved session capacities (current vs superseded in session_history), participant preferences, per-cycle allocations with agent status separate from my confirmation, waitlist order, notice idempotency keys and send outcomes, processed file hashes, working-state checkpoints, and a timestamped action log.

Restart demo: after cycle 1 the process is fully stopped. Cycle 2 supplies only the update file. Cycle 3, after another restart, supplies only the late-registration file. The original eight-row list is not re-uploaded; P01–P10 reload from SQLite and P11 is added.

Correction: I approve shrinking Agent Clinic from 4 to 3 seats. The old capacity stays in history; the next calculator uses 3. Isolation: EVT-POSTER participant Z01 cannot be retrieved while reviewing EVT-OPENDAY. Re-ingesting the same file hash creates no duplicate people or notices. Excel is a review export and never overwrites my organizer decision columns.

## Tools and access plan

Python Streamlit app plus CLI. Groq free-tier LLM (`llama-3.3-70b-versatile`); API key in `.env` or the Setup page, never in code. No paid APIs.

Tools: (1) registration reader over local CSV/PDF/JSON, content treated as untrusted; (2) policy search over a local approved policy file; (3) deterministic capacity calculator and waitlist promotion; (4) SQLite allocation/notice store with idempotency keys (persistent write); (5) notice writer: UNSENT drafts by default, optional SMTP to an allowlisted owned inbox after my approval, logging delivery vs failure separately; (6) Excel register via openpyxl that preserves manual columns.

All attendees are fictional. Instructions planted in registration notes cannot change capacity, recipients, event identity or policy. Every tool call, memory read/write, approval, error and timestamp is logged.
