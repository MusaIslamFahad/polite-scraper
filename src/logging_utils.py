"""
Extra — structured logs.

Plain print() lines are fine for a human watching the terminal, but they're
hard to grep or feed into another tool. This writes one JSON object per
line (a "JSON Lines" file) with named fields, to both the terminal and
logs/scrape.jsonl, so both a person and a program can search them.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def log_event(event: str, path: Path, **fields) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    line = json.dumps(record, ensure_ascii=False)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    print(line, file=sys.stderr)
