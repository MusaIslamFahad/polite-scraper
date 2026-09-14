"""
Stage 1 + politeness layer used by every stage that talks to the network.

Contract:
    fetch(url, cache_file) -> FetchResult

Rules encoded here (Stage 0/1/5 of the assignment, plus the "retry like a
pro" extra):
  * every real request sends an honest User-Agent
  * every real request has a timeout — it must give up, never hang forever
  * we check the status code before doing anything else with the body
  * a saved copy on disk (the cache) is read instead of re-asking the site
  * 404 and 403 are never retried — asking again will not change the answer
  * 429 and 5xx ARE retried, with real exponential backoff + jitter
    (src/retry.py), honouring a Retry-After header when the server sends one
  * every attempt, retry, and give-up is written as a structured JSON-line
    log entry (src/logging_utils.py), not just a print()
  * the caller is responsible for the inter-request delay (see main.py),
    because that delay must NOT apply to cache hits
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from . import config
from .logging_utils import log_event
from .retry import compute_backoff_seconds

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
NON_RETRYABLE_STATUSES = {403, 404}


@dataclass
class FetchResult:
    url: str
    ok: bool                 # True only for a real 200 (cached or fresh)
    from_cache: bool
    status_code: Optional[int]
    html: Optional[str]
    error: Optional[str] = None  # short human reason when ok is False


def _cache_path_for(url: str, cache_dir: Path) -> Path:
    """Deterministic, filesystem-safe cache filename for a URL."""
    safe = url.split("://", 1)[-1]
    for ch in ("/", "?", "&", ":"):
        safe = safe.replace(ch, "_")
    return cache_dir / f"{safe}.html"


def fetch(url: str, cache_dir: Path = config.CACHE_DIR, use_cache: bool = True) -> FetchResult:
    """
    Fetch one URL politely, with an on-disk cache.

    Returns a FetchResult. Never raises for ordinary network problems —
    those come back as ok=False with a reason, so the caller (main.py /
    Stage 5) can log-and-skip instead of crashing the whole run.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path_for(url, cache_dir)

    if use_cache and cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        print(f"CACHE HIT {url} ({len(html)} bytes)")
        return FetchResult(url=url, ok=True, from_cache=True, status_code=200, html=html)

    headers = {"User-Agent": config.USER_AGENT}
    attempt = 0
    last_error = None

    while attempt < config.MAX_RETRIES + 1:
        attempt += 1
        retry_after_header = None
        try:
            resp = requests.get(url, headers=headers, timeout=config.TIMEOUT_SECONDS)
        except requests.exceptions.Timeout:
            last_error = "timeout"
            log_event("fetch_timeout", config.LOG_FILE, url=url, attempt=attempt)
        except requests.exceptions.RequestException as exc:
            last_error = f"connection error: {exc}"
            log_event("fetch_connection_error", config.LOG_FILE, url=url, attempt=attempt, error=str(exc))
        else:
            log_event("fetch_attempt", config.LOG_FILE, url=url, attempt=attempt, status=resp.status_code)

            if resp.status_code == 200:
                html = resp.text
                cache_file.write_text(html, encoding="utf-8")
                print(f"FETCH {url} -> 200 ({len(html)} bytes)")
                return FetchResult(url=url, ok=True, from_cache=False, status_code=200, html=html)

            if resp.status_code in NON_RETRYABLE_STATUSES:
                # 404 = gone, asking again won't help. 403 = the site said
                # no, and asking again is how a polite robot becomes a pest.
                print(f"FETCH {url} -> {resp.status_code} (not retrying)")
                log_event("fetch_gave_up", config.LOG_FILE, url=url, attempt=attempt,
                          status=resp.status_code, reason="non_retryable_status")
                return FetchResult(
                    url=url, ok=False, from_cache=False, status_code=resp.status_code,
                    html=None, error=f"HTTP {resp.status_code}",
                )

            if resp.status_code in RETRYABLE_STATUSES:
                last_error = f"HTTP {resp.status_code}"
                retry_after_header = resp.headers.get("Retry-After")
            else:
                # Any other non-200: treat as a failed fetch, not HTML to parse.
                print(f"FETCH {url} -> {resp.status_code} (not retrying)")
                log_event("fetch_gave_up", config.LOG_FILE, url=url, attempt=attempt,
                          status=resp.status_code, reason="unhandled_status")
                return FetchResult(
                    url=url, ok=False, from_cache=False, status_code=resp.status_code,
                    html=None, error=f"HTTP {resp.status_code}",
                )

        if attempt < config.MAX_RETRIES + 1:
            wait_seconds = compute_backoff_seconds(attempt, retry_after_header=retry_after_header)
            obeyed_retry_after = retry_after_header is not None
            print(f"RETRY {url} after '{last_error}', waiting {wait_seconds}s"
                  f"{' (Retry-After header)' if obeyed_retry_after else ' (exponential backoff)'}")
            log_event("fetch_retry", config.LOG_FILE, url=url, attempt=attempt,
                      wait_seconds=wait_seconds, reason=last_error,
                      obeyed_retry_after=obeyed_retry_after)
            time.sleep(wait_seconds)

    print(f"FETCH {url} -> failed permanently after {attempt} attempts ({last_error})")
    log_event("fetch_gave_up", config.LOG_FILE, url=url, attempt=attempt,
              status=None, reason=last_error)
    return FetchResult(url=url, ok=False, from_cache=False, status_code=None, html=None, error=last_error)
