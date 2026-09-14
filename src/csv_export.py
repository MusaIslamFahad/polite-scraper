"""
Extra — CSV export.

Every field in BookRecord is already scalar (no nested objects/lists), so
nothing needs flattening in the usual "nested JSON -> columns" sense. The
one thing that does need care is `description`: it's free text that can
contain commas, quotes, or newlines, so we let Python's csv module do the
quoting instead of hand-rolling it — that's the "which values had to be
flattened" note for this dataset.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from .schema import BookRecord

CSV_COLUMNS = [
    "title", "product_url", "price_text", "price_gbp",
    "availability_text", "availability_count", "in_stock",
    "rating_text", "rating_stars", "description",
    "source_page", "fetched_at",
]


def write_csv(records: List[BookRecord], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.model_dump())
    return len(records)
