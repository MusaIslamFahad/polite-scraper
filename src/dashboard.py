"""
Extra — a tiny local dashboard.

One self-contained HTML file, no server, no CDN dependency (so it still
works with no internet at all): open it straight from the filesystem.
Data is embedded at generation time as a JSON blob, not fetched via AJAX,
because `file://` pages can't reliably fetch a sibling file in every browser.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .schema import BookRecord

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>The polite scraper — run dashboard</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 2rem;
          background: #f6f7f9; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 0.25rem; }}
  .subtitle {{ color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: white; border-radius: 10px; padding: 1rem 1.25rem;
           box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .card .value {{ font-size: 1.6rem; font-weight: 700; }}
  .card .label {{ font-size: 0.8rem; color: #666; margin-top: 0.15rem; }}
  .card.warn .value {{ color: #b45309; }}
  .card.bad .value {{ color: #b91c1c; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px;
           overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #eee; font-size: 0.85rem; }}
  th {{ background: #fafafa; color: #444; }}
  tr:last-child td {{ border-bottom: none; }}
  .muted {{ color: #999; }}
</style>
</head>
<body>
  <h1>The polite scraper — run dashboard</h1>
  <div class="subtitle">Generated {generated_at} · read straight from output/books.json + output/run-report.json</div>

  <div class="cards">
    <div class="card"><div class="value">{record_count}</div><div class="label">valid records</div></div>
    <div class="card"><div class="value">£{price_min:.2f}–£{price_max:.2f}</div><div class="label">price range (avg £{price_avg:.2f})</div></div>
    <div class="card {failed_class}"><div class="value">{failed_pages}</div><div class="label">failed pages</div></div>
    <div class="card"><div class="value">{last_fresh}</div><div class="label">data last fetched</div></div>
  </div>

  <table>
    <thead><tr><th>Title</th><th>Price</th><th>Rating</th><th>Availability</th></tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>

  <script>
    // Raw data embedded for anyone who wants to poke at it in devtools —
    // this page never makes a network request of its own.
    window.__SCRAPE_DATA__ = {data_json};
  </script>
</body>
</html>
"""

ROW_TEMPLATE = "<tr><td>{title}</td><td>£{price:.2f}</td><td>{rating}</td><td>{availability}</td></tr>"


def build_dashboard_html(records: List[BookRecord], report: dict, generated_at: str) -> str:
    if records:
        prices = [r.price_gbp for r in records]
        price_min, price_max = min(prices), max(prices)
        price_avg = sum(prices) / len(prices)
        last_fresh = max(r.fetched_at for r in records)
    else:
        price_min = price_max = price_avg = 0.0
        last_fresh = "n/a"

    failed_pages = report.get("failed_pages_count", 0)
    failed_class = "bad" if failed_pages else ("warn" if failed_pages else "")

    rows = "\n      ".join(
        ROW_TEMPLATE.format(
            title=r.title, price=r.price_gbp,
            rating=r.rating_text or "—",
            availability=r.availability_text,
        )
        for r in records
    ) or '<tr><td colspan="4" class="muted">No records yet — run python -m src.main first.</td></tr>'

    return TEMPLATE.format(
        generated_at=generated_at,
        record_count=len(records),
        price_min=price_min, price_max=price_max, price_avg=price_avg,
        failed_pages=failed_pages, failed_class=failed_class,
        last_fresh=last_fresh,
        rows=rows,
        data_json=json.dumps([r.model_dump() for r in records], ensure_ascii=False),
    )


def write_dashboard(records: List[BookRecord], report: dict, path: Path, generated_at: Optional[str] = None) -> None:
    from datetime import datetime, timezone
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_dashboard_html(records, report, generated_at), encoding="utf-8")
