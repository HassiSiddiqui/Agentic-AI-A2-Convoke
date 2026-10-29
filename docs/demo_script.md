# 8–10 minute live demonstration

Student 23i-2654 · Convoke · A14

1. **Onboarding (1 min).** Hall page empty → Load sample halls. Two events appear. Show sessions with capacity 4/4.
2. **Initial action (2 min).** Review cycle 1, `registrations_cycle1.csv`. Show five Prompting Studio requests, four confirmed, one waitlist. Point at remaining seats JSON and Excel path.
3. **Later update (1.5 min).** Cycle 2 file: P02 CANCEL, P09 injection, P10 missing preference. Show next action changing toward waitlist / clarification. Show injection badge.
4. **Restart (1.5 min).** Stop Streamlit. Start again. Do not re-upload cycle 1. Cycle 3 only. P01 still in Ledger. P11 appears.
5. **Correction (1 min).** Approvals → SESS-B capacity 3. Ledger history keeps 4. Run another cycle; remaining B uses 3.
6. **Failure / conflict (1.5 min).** Toggle simulate allocation write failure, run, show error, retry without duplicate. Isolation probe: EVT-POSTER vs Open Day.
7. **Log inspection (1 min).** Ledger action log timestamps. Dispatches: UNSENT drafts. Setup: internet rules.

If Groq is down, say so: fallback planner still seats people; the viva still shows tools and SQLite.
