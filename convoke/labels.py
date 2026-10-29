"""Plain-language labels for the Streamlit UI."""

ACTION_LABELS = {
    "ingest_registrations": "Read the registration file",
    "calculate_capacity": "Count remaining seats",
    "promote_waitlist": "Move someone off the waitlist",
    "draft_confirmation": "Draft confirmation notices",
    "waitlist_and_notify": "Waitlist overflow and notify",
    "ask_clarification": "Ask for a missing detail",
    "wait": "Wait — no notice needed yet",
    "export_register": "Update the Excel register",
}

STATUS_LABELS = {
    "Not started": "Registered, no seat yet",
    "In progress": "Waitlisted / still open",
    "Evidence supports completion": "Seat available — suggest confirm",
    "Delayed": "Cancelled or delayed",
    "Needs review": "Needs your review",
}

PAGES = [
    ("Home", "Overview"),
    ("Create event", "Save the two sessions"),
    ("Run review", "Seat people for a cycle"),
    ("Confirm seats", "Your decisions"),
    ("Notices", "Unsent drafts / email"),
    ("Records", "Memory, logs, Excel"),
    ("Settings", "Groq key and SMTP"),
]


def action_label(value: str | None) -> str:
    if not value:
        return "—"
    return ACTION_LABELS.get(value, value.replace("_", " "))


def status_label(value: str | None) -> str:
    if not value:
        return "—"
    return STATUS_LABELS.get(value, value)
