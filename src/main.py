"""
The polite scraper — orchestrator.

    python -m src.main

runs the full pipeline: discover the first 3 catalogue pages, visit all
book pages, extract, normalize, validate, store, report. See README.md
for the documented run command and flags.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from . import config
from .change_detection import compute_hashes, diff_against_previous, load_previous_hashes, save_hashes
from .crawler import discover
from .csv_export import write_csv
from .dashboard import write_dashboard
from .extractor import extract_raw_record
from .fetcher import fetch
from .normalizer import normalize
from .report import RunStats, write_report
from .schema import validate_record
from .storage import write_books_json, write_errors_json


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="The polite scraper (FlyRank BE-05)")
    parser.add_argument(
        "--base-url", default=config.BASE_URL,
        help="Override the target base URL (used for local demo/testing only).",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Ignore any cached pages and re-fetch everything from the network.",
    )
    parser.add_argument(
        "--inject-broken-url", action="store_true",
        help="Add one made-up book URL on purpose, to prove Stage 5 survives it.",
    )
    parser.add_argument(
        "--skip-extras", action="store_true",
        help="Skip the optional extras (CSV export, change detection, dashboard) — core pipeline only.",
    )
    return parser


def polite_fetch(url: str, use_cache: bool, stats: RunStats):
    """Wraps fetcher.fetch with the inter-request delay and stats bookkeeping."""
    result = fetch(url, use_cache=use_cache)
    if result.from_cache:
        stats.cache_hits += 1
    else:
        stats.fetched_from_network += 1
        # Only real network hits need to be polite about pacing.
        time.sleep(config.REQUEST_DELAY_SECONDS)
    return result


def run(base_url: str = config.BASE_URL, use_cache: bool = True,
        inject_broken_url: bool = False, run_extras: bool = True) -> dict:
    stats = RunStats()

    # --- Stage 2: discover the first 3 catalogue pages + every book URL -----
    crawl_result = discover(lambda u: polite_fetch(u, use_cache, stats), base_url=base_url)
    stats.catalogue_pages_fetched = len(crawl_result.catalogue_pages)

    book_urls = list(crawl_result.book_urls)
    if inject_broken_url:
        book_urls.append(f"{base_url.rstrip('/')}/catalogue/this-book-does-not-exist_00000/index.html")

    print(
        f"catalogue_pages={stats.catalogue_pages_fetched} "
        f"discovered={len(book_urls)} unique_urls={len(set(book_urls))}"
    )

    # --- Stage 3 + 4: fetch, extract, normalize, validate every book page ----
    valid_records = []
    errors = []

    for url in book_urls:
        stats.book_pages_attempted += 1
        fetch_result = polite_fetch(url, use_cache, stats)

        if not fetch_result.ok:
            # Stage 5: one bad page is logged and skipped, never crashes the run.
            reason = fetch_result.error or "unknown fetch error"
            errors.append({"url": url, "stage": "fetch", "reason": reason})
            stats.failed_pages.append({"url": url, "reason": reason})
            stats.invalid_records += 1
            continue

        # True provenance: the specific catalogue page this book URL was found
        # on, not just "whichever page we happened to fetch last".
        source_page = crawl_result.source_page_by_url.get(url, base_url)
        fetched_at = datetime.now(timezone.utc).isoformat()
        raw = extract_raw_record(fetch_result.html, product_url=url, source_page=source_page, fetched_at=fetched_at)
        clean = normalize(raw)

        record, reason = validate_record(clean)
        if record is None:
            errors.append({"url": url, "stage": "validate", "reason": reason})
            stats.invalid_records += 1
        else:
            valid_records.append(record)

    stats.valid_records = len(valid_records)

    # --- Stage 4: store -------------------------------------------------------
    saved_count = write_books_json(valid_records, config.BOOKS_JSON)
    write_errors_json(errors, config.ERRORS_JSON)

    # --- Stage 5: report --------------------------------------------------------
    report = write_report(stats, config.RUN_REPORT_JSON)

    print(f"books.json: {saved_count} records | errors.json: {len(errors)} | "
          f"failed_pages: {report['failed_pages_count']}")

    # --- Extras: CSV export, change detection, dashboard -------------------------
    if run_extras:
        write_csv(valid_records, config.BOOKS_CSV)

        current_hashes = compute_hashes(valid_records)
        previous_hashes = load_previous_hashes(config.PREVIOUS_HASHES_JSON)
        change_report = diff_against_previous(current_hashes, previous_hashes)
        config.CHANGE_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        config.CHANGE_REPORT_JSON.write_text(json.dumps(change_report, indent=2), encoding="utf-8")
        save_hashes(current_hashes, config.PREVIOUS_HASHES_JSON)

        write_dashboard(valid_records, report, config.DASHBOARD_HTML)

        print(f"books.csv: {len(valid_records)} rows | "
              f"changed since last run: +{change_report['new']} ~{change_report['changed']} "
              f"={change_report['unchanged']} -{change_report['gone']} | "
              f"dashboard.html written")

    return report


def main() -> None:
    args = build_arg_parser().parse_args()
    run(base_url=args.base_url, use_cache=not args.no_cache,
        inject_broken_url=args.inject_broken_url, run_extras=not args.skip_extras)


if __name__ == "__main__":
    main()
