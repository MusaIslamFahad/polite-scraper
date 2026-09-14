"""
Stage 2 — find all three catalogue pages and every book link on them.

We never hardcode "60 book links". We follow the catalogue's own "next"
link, starting from page 1, and stop once we've visited CATALOGUE_PAGE_COUNT
pages or the site itself runs out of "next" links (whichever comes first).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from . import config


@dataclass
class CrawlResult:
    catalogue_pages: List[str] = field(default_factory=list)
    book_urls: List[str] = field(default_factory=list)  # de-duplicated, absolute, in order
    # provenance: which catalogue page each book URL was actually found on
    # (the FIRST page it was seen on, if it somehow appeared on more than one)
    source_page_by_url: Dict[str, str] = field(default_factory=dict)


def parse_catalogue_page(html: str, page_url: str) -> tuple[list[str], str | None]:
    """
    Given one catalogue page's HTML, return (book_urls_on_this_page, next_url_or_None).
    Both are absolute URLs, resolved with urljoin — never by gluing strings together.
    """
    soup = BeautifulSoup(html, "html.parser")

    book_urls = []
    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        if link and link.get("href"):
            book_urls.append(urljoin(page_url, link["href"]))

    next_link = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_link["href"]) if next_link and next_link.get("href") else None

    return book_urls, next_url


def discover(fetch_fn, base_url: str = config.BASE_URL) -> CrawlResult:
    """
    Walk the catalogue starting at page 1, using `fetch_fn(url) -> FetchResult`
    (injected so this function never has to know about caching or requests).

    `base_url` defaults to the real site but can be pointed at a local mirror
    for offline testing — nothing else in this function changes.

    Stops after config.CATALOGUE_PAGE_COUNT pages, or earlier if the site
    itself has no more "next" link.
    """
    result = CrawlResult()
    seen = set()

    page_url = f"{base_url.rstrip('/')}/catalogue/page-1.html"
    for _ in range(config.CATALOGUE_PAGE_COUNT):
        fetch_result = fetch_fn(page_url)
        if not fetch_result.ok:
            # A broken catalogue page is still "one bad page" — log and stop
            # walking further, but keep whatever we already found.
            print(f"WARN: could not load catalogue page {page_url}: {fetch_result.error}")
            break

        result.catalogue_pages.append(page_url)
        urls, next_url = parse_catalogue_page(fetch_result.html, page_url)

        for url in urls:
            if url not in seen:
                seen.add(url)
                result.book_urls.append(url)
                result.source_page_by_url[url] = page_url  # true provenance, not "whatever page we ended on"

        if not next_url:
            break
        page_url = next_url

    return result
