"""
Stretch — browser cost comparison.

Fetches https://quotes.toscrape.com/js once with plain requests, and once
with Playwright, and reports time + memory for both. This is the concrete
evidence behind the README line "why this assignment needed no browser":
books.toscrape.com sends the data in the first response; quotes.toscrape.com/js
deliberately does NOT, to make the point for us.

Verified by hand first (see README "Verification" section): fetching
https://quotes.toscrape.com/js with a plain HTTP request returns the page
chrome (title, nav, footer) and zero quote text — the quotes only exist
after the page's JavaScript runs.

Run:
    pip install playwright
    playwright install chromium   # downloads a real browser binary — several
                                   # hundred MB, needs normal internet access
    python -m tools.browser_cost_compare
"""

from __future__ import annotations

import time
import tracemalloc

import requests

URL = "https://quotes.toscrape.com/js/"


def fetch_plain() -> dict:
    tracemalloc.start()
    t0 = time.perf_counter()
    resp = requests.get(URL, timeout=10)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    quote_count = resp.text.count('class="quote"')
    return {
        "method": "plain requests.get",
        "elapsed_seconds": round(elapsed, 3),
        "peak_python_memory_kb": round(peak / 1024, 1),
        "quotes_found": quote_count,
    }


def fetch_with_playwright() -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "method": "playwright",
            "error": "playwright not installed — `pip install playwright && playwright install chromium`",
        }

    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(URL)
            page.wait_for_selector(".quote")
            quote_count = page.locator(".quote").count()
            browser.close()
    except Exception as exc:  # browser binary missing, etc. — report, don't crash
        tracemalloc.stop()
        return {"method": "playwright", "error": str(exc)}

    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "method": "playwright (chromium)",
        "elapsed_seconds": round(elapsed, 3),
        "peak_python_memory_kb": round(peak / 1024, 1),
        "quotes_found": quote_count,
    }


def main() -> None:
    plain = fetch_plain()
    print("Plain HTTP:", plain)

    browser = fetch_with_playwright()
    print("Playwright:", browser)

    if "error" not in browser:
        print(
            f"\nSummary: plain HTTP found {plain['quotes_found']} quotes in "
            f"{plain['elapsed_seconds']}s; Playwright found {browser['quotes_found']} "
            f"quotes in {browser['elapsed_seconds']}s "
            f"({browser['elapsed_seconds'] / max(plain['elapsed_seconds'], 0.001):.0f}x slower), "
            f"using {browser['peak_python_memory_kb']}KB vs {plain['peak_python_memory_kb']}KB "
            "of Python-side memory (Playwright's own browser process uses far more on top of that)."
        )
    else:
        print(f"\nCouldn't run the Playwright half here: {browser['error']}")


if __name__ == "__main__":
    main()
