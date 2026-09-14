"""
Extra — retry like a pro: the backoff math, isolated so it can be unit
tested without any real network calls or real time.sleep().
"""

from __future__ import annotations

import random
from typing import Optional


def parse_retry_after(header_value: Optional[str]) -> Optional[float]:
    """
    Retry-After is usually a plain integer number of seconds. It can also
    be an HTTP-date, which we deliberately don't parse here (rare in
    practice for this kind of API, and getting timezone-aware HTTP-date
    parsing wrong is worse than falling back to our own backoff).
    """
    if not header_value:
        return None
    try:
        seconds = float(header_value.strip())
        return seconds if seconds >= 0 else None
    except ValueError:
        return None


def compute_backoff_seconds(
    attempt: int,
    retry_after_header: Optional[str] = None,
    base_seconds: float = 1.0,
    cap_seconds: float = 30.0,
    jitter_fraction: float = 0.25,
    rng: Optional[random.Random] = None,
) -> float:
    """
    If the server told us exactly how long to wait (Retry-After), obey it —
    no guessing, no jitter added on top of an explicit instruction.

    Otherwise: exponential backoff (1s, 2s, 4s, 8s, ...) capped at
    cap_seconds, with a little randomness added so a whole fleet of
    retrying clients doesn't all hammer the server at the exact same
    instant (the "thundering herd" problem).
    """
    retry_after = parse_retry_after(retry_after_header)
    if retry_after is not None:
        return retry_after

    rng = rng or random
    raw = min(base_seconds * (2 ** (attempt - 1)), cap_seconds)
    jitter = raw * jitter_fraction * rng.random()
    return round(raw + jitter, 3)
