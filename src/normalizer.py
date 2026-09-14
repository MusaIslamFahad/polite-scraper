"""
Stage 4 (part 1) — raw strings are ingredients, this file is the prep work.

Every function here is pure and easy to unit-test: text in, a typed value
(or None) out. Nothing here touches the network, the filesystem, or the schema.
"""

from __future__ import annotations

import re
from typing import Optional

from . import config

_PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)")
_AVAILABILITY_COUNT_RE = re.compile(r"\((\d+)\s+available\)", re.IGNORECASE)


def parse_price_gbp(price_text: Optional[str]) -> Optional[float]:
    """
    '£51.77' -> 51.77
    Deliberately currency-symbol agnostic: it pulls the first number out of
    the string rather than assuming a '£' will always be first, since stray
    encoding artifacts (e.g. a mis-decoded '£' byte) must not crash a run.
    """
    if not price_text:
        return None
    match = _PRICE_RE.search(price_text)
    return float(match.group(1)) if match else None


def parse_availability(availability_text: Optional[str]) -> tuple[bool, Optional[int]]:
    """
    'In stock (22 available)' -> (True, 22)
    'In stock'                -> (True, None)
    'Out of stock'            -> (False, None)
    None                      -> (False, None)
    """
    if not availability_text:
        return False, None
    in_stock = "in stock" in availability_text.lower()
    match = _AVAILABILITY_COUNT_RE.search(availability_text)
    count = int(match.group(1)) if match else None
    return in_stock, count


def rating_to_stars(rating_text: Optional[str]) -> Optional[int]:
    """'Three' -> 3. Unknown/missing words come back as None, never guessed."""
    if not rating_text:
        return None
    return config.RATING_WORDS.get(rating_text)


def normalize(raw: dict) -> dict:
    """
    Take one raw record (extractor.py's output) and return a clean record
    with the original text kept side by side with the parsed value, per the
    assignment's "raw and clean live side by side" rule.
    """
    in_stock, availability_count = parse_availability(raw.get("availability_text"))

    return {
        **raw,
        "price_gbp": parse_price_gbp(raw.get("price_text")),
        "in_stock": in_stock,
        "availability_count": availability_count,
        "rating_stars": rating_to_stars(raw.get("rating_text")),
    }
