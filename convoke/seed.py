from __future__ import annotations

import json

from convoke.onboard import onboard_event
from convoke.paths import SAMPLES
from convoke.store import init_db


def load_event(name: str) -> dict:
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def seed_demo() -> dict:
    init_db()
    open_day = load_event("event_baseline.json")
    poster = load_event("event_isolation.json")
    a = onboard_event(**open_day)
    b = onboard_event(**poster)
    return {"open_day": a, "poster": b}
