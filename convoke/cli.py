from __future__ import annotations

import argparse
import json

from convoke.agent import run_cycle
from convoke.config import Settings
from convoke.paths import SAMPLES
from convoke.seed import seed_demo
from convoke.store import init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Convoke academic event coordinator")
    parser.add_argument("command", choices=["seed", "cycle", "evaluate"])
    parser.add_argument("--event", default="EVT-OPENDAY")
    parser.add_argument("--cycle", type=int, default=1)
    parser.add_argument("--file", default="")
    parser.add_argument("--no-memory", action="store_true")
    args = parser.parse_args()
    init_db()
    if args.command == "seed":
        print(json.dumps(seed_demo(), indent=2))
        return
    if args.command == "evaluate":
        from convoke.evaluate import run_evaluation

        print(json.dumps(run_evaluation(), indent=2))
        return
    path = args.file or str(SAMPLES / "registrations_cycle1.csv")
    result = run_cycle(
        Settings(),
        args.event,
        args.cycle,
        source_paths=[path],
        memory_enabled=not args.no_memory,
    )
    print(json.dumps({
        "next_action": result["plan"].get("next_action"),
        "remaining": result["capacity"].get("remaining"),
        "recorded": result["recorded"],
        "fallback": result["plan"].get("fallback"),
        "register": result["register_path"],
    }, indent=2))
