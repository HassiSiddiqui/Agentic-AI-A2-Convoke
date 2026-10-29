# Convoke memory schema

Authoritative store: `data/store/convoke.sqlite`.

Excel under `outputs/` is a review export. Re-export reads organizer decision columns from the previous workbook so teacher/organizer comments are not overwritten.

## Tables

| Table | Why it exists | Retrieved when | Who may change it |
| --- | --- | --- | --- |
| `events` | Stable event identity and venue | Every cycle | Organizer onboard |
| `sessions` | Current approved capacity and timetable | Capacity tool | Organizer correction |
| `session_history` | Superseded capacities and times | Correction / audit | Append-only |
| `participants` | People and last stated preference | Planning | Ingest (untrusted text sanitised) |
| `allocations` | Per-cycle suggested status and evidence | UI, Excel, later cycles | Agent write; organizer status is a separate column |
| `waitlist` | Overflow order | Later cycle after a cancellation | Agent write |
| `notices` | Draft/sent mail with idempotency keys | Retry, dispatch tab | Agent write after policy checks |
| `processed_sources` | File hashes and injection flags | Ingest | Append-only |
| `working_state` | Current goal, plan checkpoint, pending question | Restart | Agent checkpoint |
| `action_log` | Tool calls, memory IO, errors, timestamps | Ledger / viva | Append-only |

## Lifecycle

- **Save:** after a successful tool call, with timestamps and source hashes.
- **Retrieve:** at the start of every cycle unless `--no-memory` / the UI toggle is off.
- **Correct:** `tool_update_session_fact` writes history then updates the current row.
- **Delete:** not exposed in the UI. A DBA can delete by `event_id` to drop a hall.
- **Access:** one organizer demo user; queries always include `event_id`.

Projects are isolated by `event_id`. `EVT-POSTER` cannot be read while reviewing `EVT-OPENDAY` unless the UI isolation probe is pointed at it on purpose.
