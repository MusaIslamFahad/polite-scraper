"""
Stage 4 (part 3) — can another program use this?

Design choice for idempotency: each run builds one fresh, de-duplicated
list of valid records (keyed by product_url, the canonical identity) and
*overwrites* books.json with it. We never append to the previous run's
file. That makes "run it twice, get the same 60 records, not 120" true
by construction, with no merge logic to get wrong.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .schema import BookRecord


def dedupe_by_url(records: Iterable[BookRecord]) -> list[BookRecord]:
    seen = set()
    unique = []
    for record in records:
        if record.product_url not in seen:
            seen.add(record.product_url)
            unique.append(record)
    return unique


def write_books_json(records: list[BookRecord], path: Path) -> int:
    unique = dedupe_by_url(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [r.model_dump() for r in unique]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(unique)


def write_errors_json(errors: list[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(errors)
