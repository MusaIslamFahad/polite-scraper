"""
AI-version, rematch (v2) — generated from PROMPT_V2.md, which adds the four
fixes found by actually running v1 against real test scenarios (see
../AI_VS_ME.md). This is NOT hand-patched from v1 line by line — it's a
fresh generation from the improved prompt, same as v1 was from the original.
"""

import json
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com"
HEADERS = {"User-Agent": "BooksScraperBot/1.0 (student project)"}
OUTPUT_FILE = "output_ai_v2/books.json"
FAILED_FILE = "output_ai_v2/failed.json"
REPORT_FILE = "output_ai_v2/run-report.json"
DELAY = 1
MAX_RETRIES = 2
TIMEOUT = 8
RETRYABLE_STATUSES = {500, 502, 503, 504}
NON_RETRYABLE_STATUSES = {403, 404}


def get_page(url):
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        except requests.exceptions.Timeout:
            print(f"Timeout on {url}, retrying...")
            time.sleep(DELAY)
            continue
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}, retrying...")
            time.sleep(DELAY)
            continue

        if resp.status_code == 200:
            return resp.text
        if resp.status_code in NON_RETRYABLE_STATUSES:
            print(f"Got {resp.status_code} for {url} — not retrying, that won't change.")
            return None
        if resp.status_code in RETRYABLE_STATUSES:
            print(f"Got {resp.status_code} for {url}, retrying...")
            time.sleep(DELAY)
            continue
        print(f"Unexpected status {resp.status_code} for {url}, not retrying.")
        return None

    print(f"Giving up on {url}")
    return None


def get_catalogue_urls():
    book_urls = []
    url = f"{BASE_URL}/catalogue/page-1.html"
    pages_visited = 0

    while pages_visited < 3:
        html = get_page(url)
        if html is None:
            break
        soup = BeautifulSoup(html, "html.parser")
        pages_visited += 1

        for card in soup.select("article.product_pod"):
            link = card.select_one("h3 a")
            book_urls.append(urljoin(url, link["href"]))

        next_link = soup.select_one("li.next a")
        if not next_link:
            break
        url = urljoin(url, next_link["href"])
        time.sleep(DELAY)

    return book_urls


def parse_price(text):
    cleaned = text.replace("£", "").strip()
    return float(cleaned)


def scrape_book(url, source_page):
    html = get_page(url)
    if html is None:
        return None

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1").text
    price_gbp = parse_price(soup.find("p", class_="price_color").text)
    availability_text = soup.find("p", class_="instock").text.strip()

    rating_tag = soup.find("p", class_="star-rating")
    rating = rating_tag["class"][1] if rating_tag else None

    # Fix #1: a book might not have a description block at all.
    desc_div = soup.find("div", id="product_description")
    if desc_div is not None:
        desc_p = desc_div.find_next_sibling("p")
        description = desc_p.text.strip() if desc_p else None
    else:
        description = None

    return {
        "title": title,
        "product_url": url,
        "price_gbp": price_gbp,
        "availability_text": availability_text,
        "rating": rating,
        "description": description,
        "source_page": source_page,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def load_existing_books():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return []


def main():
    os.makedirs("output_ai_v2", exist_ok=True)

    book_urls = get_catalogue_urls()
    print(f"Found {len(book_urls)} books across the first 3 pages")

    # Fix #3: keep previously-seen books in a dict keyed by URL, and
    # OVERWRITE each one with today's scrape — a rerun refreshes, not just appends.
    existing = {b["product_url"]: b for b in load_existing_books()}

    failed = []
    refreshed_count = 0

    for url in book_urls:
        record = scrape_book(url, source_page=BASE_URL)
        if record is None:
            failed.append(url)
            continue

        try:
            float(record["price_gbp"])
        except (TypeError, ValueError):
            failed.append(url)
            continue

        existing[url] = record  # insert if new, overwrite if already seen
        refreshed_count += 1
        time.sleep(DELAY)

    books = list(existing.values())

    with open(OUTPUT_FILE, "w") as f:
        json.dump(books, f, indent=2)

    with open(FAILED_FILE, "w") as f:
        json.dump(failed, f, indent=2)

    report = {
        "pages_checked": 3,
        "books_found": len(book_urls),
        "books_refreshed_this_run": refreshed_count,
        "total_books_saved": len(books),
        "failed": len(failed),
    }
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Done. {len(books)} total books saved, {len(failed)} failed.")


if __name__ == "__main__":
    main()
