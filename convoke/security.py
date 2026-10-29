"""Treat every ingested document, email, and CSV cell as untrusted content."""

from __future__ import annotations

import re
from dataclasses import dataclass

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"you are now",
    r"system prompt",
    r"override (the )?(policy|permissions|allowlist|recipient)",
    r"send (this )?to ",
    r"change (the )?(event|session|capacity|recipient|policy)",
    r"approve (all|everyone|this request)",
    r"grant (vip|unlimited) (access|seats?)",
    r"exfiltrat",
    r"do not log",
    r"new tool permissions",
]


@dataclass
class SanitizedText:
    original: str
    cleaned: str
    flagged: bool
    matches: list[str]


def sanitize_untrusted(text: str | None) -> SanitizedText:
    original = text or ""
    matches = []
    lowered = original.lower()
    for pattern in INJECTION_PATTERNS:
        found = re.findall(pattern, lowered, flags=re.IGNORECASE)
        if found:
            matches.append(pattern)
    cleaned = original
    for pattern in INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[untrusted-instruction-removed]", cleaned, flags=re.IGNORECASE)
    return SanitizedText(
        original=original,
        cleaned=cleaned.strip(),
        flagged=bool(matches),
        matches=matches,
    )


def assert_not_control_field(field: str, value: str) -> None:
    """Callers must never copy untrusted text into these fields."""
    forbidden = {
        "event_id",
        "recipient",
        "allowlist",
        "smtp_password",
        "tool_permissions",
        "organizer_decision",
        "capacity",
        "policy",
    }
    if field in forbidden:
        raise ValueError(f"Untrusted content cannot write control field {field}: {value!r}")
