"""
Central configuration for the polite scraper.

Everything a reviewer would want to check at a glance — who we say we are,
how fast we go, and where things get written — lives in one place.
"""

from pathlib import Path

# --- Target -----------------------------------------------------------------
# The only site this project touches. See README "Target classification".
BASE_URL = "https://books.toscrape.com"
CATALOGUE_PAGE_COUNT = 3  # first 3 pages only = 60 books, by design (Stage 2)

# --- Politeness ---------------------------------------------------------------
# TODO: before you run this for real, put your own repo link / contact here.
USER_AGENT = "FlyRankInternshipBE05/1.0 (+https://github.com/YOUR-USERNAME/flyrank-internship-be05)"
TIMEOUT_SECONDS = 8            # a request must give up, never hang forever
REQUEST_DELAY_SECONDS = 0.6    # minimum gap between two *real* network requests
MAX_RETRIES = 3                # exponential backoff + jitter, see src/retry.py

# --- Paths --------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

BOOKS_JSON = OUTPUT_DIR / "books.json"
ERRORS_JSON = OUTPUT_DIR / "errors.json"
RUN_REPORT_JSON = OUTPUT_DIR / "run-report.json"

# --- Extras --------------------------------------------------------------------
BOOKS_CSV = OUTPUT_DIR / "books.csv"
CHANGE_REPORT_JSON = OUTPUT_DIR / "change-report.json"
PREVIOUS_HASHES_JSON = OUTPUT_DIR / ".previous_hashes.json"  # small state file, change-detection only
DASHBOARD_HTML = OUTPUT_DIR / "dashboard.html"
LOG_FILE = PROJECT_ROOT / "logs" / "scrape.jsonl"

# --- Rating text -> number, used by normalizer.py ------------------------------
RATING_WORDS = {"Zero": 0, "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
