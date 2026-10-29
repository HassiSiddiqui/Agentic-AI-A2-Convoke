from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from convoke.paths import LOGS, ensure_dirs


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class AuditLog:
    def __init__(self, path: Path | None = None) -> None:
        ensure_dirs()
        self.path = path or (LOGS / "audit.jsonl")

    def write(self, event: str, **payload) -> dict:
        record = {"timestamp": utcnow(), "event": event, **payload}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")
        return record

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
