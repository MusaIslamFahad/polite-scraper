"""
Stage 3 — turn one book detail page into a raw record.

Selectors are aimed at the product area (`div.product_main`, `#product_description`)
rather than "the first thing that looks like a price" — that trick works today
and breaks the day the page grows a second price (e.g. a "was / now" sale price).

Raw records are deliberately un-cleaned: price_text keeps its "£" sign,
rating_text is the site's own word ("Three"), etc. Cleaning happens in
normalizer.py — this file's only job is "what does the page literally say".
"""

from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup


def _clean_text(node) -> Optional[str]:
    """Collapse internal whitespace/newlines the way a person reading the page would."""
    if node is None:
        return None
    text = node.get_text(" ", strip=True)
    text = " ".join(text.split())
    return text or None


def extract_raw_record(html: str, product_url: str, source_page: str, fetched_at: str) -> dict:
    """
    Parse a book detail page's HTML into the 8 raw fields the assignment specifies.
    Never invents a value: a field that isn't on the page comes back as None.
    """
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("div.product_main")

    title = _clean_text(main.select_one("h1")) if main else None
    price_text = _clean_text(main.select_one("p.price_color")) if main else None
    availability_text = _clean_text(main.select_one("p.instock.availability")) if main else None

    rating_text = None
    if main:
        rating_node = main.select_one("p.star-rating")
        if rating_node:
            classes = rating_node.get("class", [])
            words = [c for c in classes if c != "star-rating"]
            rating_text = words[0] if words else None

    # Description: the <p> that immediately follows the #product_description
    # marker div. Some books may have no description at all -> None, never invented.
    description = None
    desc_marker = soup.select_one("#product_description")
    if desc_marker:
        desc_p = desc_marker.find_next_sibling("p")
        description = _clean_text(desc_p)

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
