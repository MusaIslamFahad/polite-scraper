"""
Extra — changed since last run.

We hash the fields that represent "the book's actual content" (price,
availability, rating, description, title) — deliberately excluding
fetched_at, since that changes on every single run and would make
everything look "changed" forever, which defeats the point.

State is kept in a small, separate file (config.PREVIOUS_HASHES_JSON).
This is the one place in the project that deliberately keeps state across
runs — everything else (books.json) is a fresh rebuild every time.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

from .schema import BookRecord


def _content_hash(record: BookRecord) -> str:
    payload = "|".join([
        record.title,
        record.price_text,
        record.availability_text,
        record.rating_text or "",
        record.description or "",
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_hashes(records: List[BookRecord]) -> Dict[str, str]:
    return {r.product_url: _content_hash(r) for r in records}


def load_previous_hashes(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_hashes(hashes: Dict[str, str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(hashes, indent=2), encoding="utf-8")


def diff_against_previous(current: Dict[str, str], previous: Dict[str, str]) -> dict:
    new_urls = sorted(set(current) - set(previous))
    gone_urls = sorted(set(previous) - set(current))
    common = set(current) & set(previous)
    changed_urls = sorted(u for u in common if current[u] != previous[u])
    unchanged_urls = sorted(u for u in common if current[u] == previous[u])

    return {
        "new": len(new_urls),
        "changed": len(changed_urls),
        "unchanged": len(unchanged_urls),
        "gone": len(gone_urls),
        "new_urls": new_urls,
        "changed_urls": changed_urls,
        "gone_urls": gone_urls,
    }
