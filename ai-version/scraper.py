"""
AI-version — generated from PROMPT.md alone, quarantined from src/.

This is what a single quick generation looks like when the prompt is a
reasonable-but-imperfect description written from memory, instead of the
full assignment spec. It mostly works. Where it doesn't, see
../AI_VS_ME.md for what broke and why.
"""

import json
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com"
HEADERS = {"User-Agent": "BooksScraperBot/1.0 (student project)"}
OUTPUT_FILE = "output_ai/books.json"
FAILED_FILE = "output_ai/failed.json"
REPORT_FILE = "output_ai/run-report.json"
DELAY = 1  # seconds between requests
MAX_RETRIES = 2


def get_page(url):
    """Fetch a URL, retrying a couple of times if it doesn't come back clean."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS)  # no explicit timeout
            if resp.status_code == 200:
                return resp.text
            print(f"Got status {resp.status_code} for {url}, retrying...")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}, retrying...")
        time.sleep(DELAY)
    print(f"Giving up on {url}")
    return None


def get_catalogue_urls():
    """Walk the first 3 catalogue pages and collect every book link."""
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
    # strip the currency symbol and convert
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

    # description lives right after the #product_description marker
    desc_div = soup.find("div", id="product_description")
    description = desc_div.find_next_sibling("p").text.strip()

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
    os.makedirs("output_ai", exist_ok=True)

    book_urls = get_catalogue_urls()
    print(f"Found {len(book_urls)} books across the first 3 pages")

    books = load_existing_books()
    existing_urls = {b["product_url"] for b in books}

    failed = []
    new_count = 0

    for url in book_urls:
        if url in existing_urls:
            continue  # already have it, don't duplicate on rerun

        record = scrape_book(url, source_page=BASE_URL)
        if record is None:
            failed.append(url)
            continue

        try:
            float(record["price_gbp"])  # sanity check it's really a number
        except (TypeError, ValueError):
            failed.append(url)
            continue

        books.append(record)
        new_count += 1
        time.sleep(DELAY)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(books, f, indent=2)

    with open(FAILED_FILE, "w") as f:
        json.dump(failed, f, indent=2)

    report = {
        "pages_checked": 3,
        "books_found": len(book_urls),
        "new_books_this_run": new_count,
        "total_books_saved": len(books),
        "failed": len(failed),
    }
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Done. {len(books)} total books saved, {len(failed)} failed.")


if __name__ == "__main__":
    main()
