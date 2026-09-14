"""
Stage 5 — did the run actually work? A scraper that reports nothing can
fail silently for weeks. This is the honest few numbers at the end of every run.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RunStats:
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    _start_perf: float = field(default_factory=time.perf_counter, repr=False)

    catalogue_pages_fetched: int = 0
    book_pages_attempted: int = 0
    cache_hits: int = 0
    fetched_from_network: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    failed_pages: list = field(default_factory=list)  # [{"url":..., "reason":...}]

    def finalize(self) -> dict:
        ended_at = datetime.now(timezone.utc).isoformat()
        duration = round(time.perf_counter() - self._start_perf, 3)
        report = {
            "started_at": self.started_at,
            "ended_at": ended_at,
            "duration_seconds": duration,
            "catalogue_pages_fetched": self.catalogue_pages_fetched,
            "book_pages_attempted": self.book_pages_attempted,
            "cache_hits": self.cache_hits,
            "fetched_from_network": self.fetched_from_network,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "failed_pages_count": len(self.failed_pages),
            "failed_pages": self.failed_pages,
        }
        return report


def write_report(stats: RunStats, path: Path) -> dict:
    report = stats.finalize()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
