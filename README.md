# The polite scraper — FlyRank BE-05

A small, polite scraping pipeline for [Books to Scrape](https://books.toscrape.com): it downloads the
first three catalogue pages, visits all 60 book pages, turns messy HTML into clean, checked JSON
records, survives a broken page without crashing, and ends every run with a short report of what
happened.

Pipeline shape: **fetch → extract → normalize → validate → store → report.**

## Target classification (Stage 0)

- **Site:** Books to Scrape — `https://books.toscrape.com`
- **Why this site is okay to scrape:** the site's own homepage says *"We love being scraped!"* — it
  is a public sandbox built specifically for people to practise scraping on.
- **Scope:** the first 3 catalogue pages only (60 books total). I do not crawl the other 997 books,
  and I do not crawl any other section of the site.
- **What I collect:** for each of the 60 books — title, price, availability, star rating,
  description, and where/when I got it (source page + fetch timestamp). No personal data, no
  accounts, no checkout flow.
- **robots.txt result:** I requested `https://books.toscrape.com/robots.txt` directly and it returns
  **HTTP 404 — no robots file found.** A missing file is not permission by itself, but combined with
  the site's own "We love being scraped!" statement and its explicit purpose as a scraping sandbox,
  scraping the public catalogue pages here is appropriate.
- **I will not reuse this code on another site without checking its rules and terms first.**

## Requirements & install

- Python 3.10+
- `pip install -r requirements.txt` (installs `requests`, `beautifulsoup4`, `pydantic`, `pytest`)

## Run it

```bash
cd scraper
pip install -r requirements.txt

# 1. Before your first real run, open src/config.py and put your own
#    GitHub repo link / contact in USER_AGENT — a polite scraper always
#    names itself honestly.

# 2. Run the full pipeline against the real site:
python -m src.main

# Run it again — the second run should read mostly from cache/ and still
# produce exactly 60 records, not 120:
python -m src.main

# Prove Stage 5 (one bad page must not kill the run) by adding one
# made-up book URL on purpose:
python -m src.main --inject-broken-url

# Run the unit tests:
pytest tests/ -v
```

Outputs land in `output/books.json`, `output/errors.json`, and `output/run-report.json`.
Cached HTML lands in `cache/` (gitignored — don't commit it).

## Project layout

```
scraper/
├── src/
│   ├── config.py       target, politeness settings, paths
│   ├── fetcher.py       Stage 1 — polite fetch + on-disk cache + retry-like-a-pro
│   ├── retry.py          backoff/Retry-After math (unit-testable, no real time.sleep)
│   ├── logging_utils.py   structured JSON-line logs
│   ├── crawler.py          Stage 2 — discover the 3 catalogue pages + book URLs
│   ├── extractor.py         Stage 3 — HTML -> raw record (8 fields)
│   ├── normalizer.py         Stage 4a — raw text -> typed values
│   ├── schema.py               Stage 4b — Pydantic BookRecord + validation
│   ├── storage.py               Stage 4c — write books.json / errors.json (idempotent)
│   ├── report.py                 Stage 5 — run-report.json
│   ├── csv_export.py              extra — books.csv
│   ├── change_detection.py         extra — new/changed/unchanged/gone
│   ├── dashboard.py                 extra — dashboard.html
│   ├── enrich.py                     extra — local AI enrichment via Ollama
│   └── main.py                        orchestrator / CLI entry point
├── tools/
│   └── browser_cost_compare.py    extra — plain HTTP vs. Playwright
├── ai-version/                      the AI-rematch bonus stage (see AI_VS_ME.md)
├── tests/                            25 unit tests (see below)
├── output/                            books.json, books.csv, errors.json, run-report.json,
│                                       change-report.json, dashboard.html
├── logs/                               gitignored — structured JSON-line logs
├── cache/                              gitignored, rebuilt by every run
└── requirements.txt
```

## Record schema

Every record in `output/books.json` looks like this. Raw text and its parsed value live side by side
(e.g. `price_text` and `price_gbp`), per Stage 4's rule.

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "availability_count": 22,
  "in_stock": true,
  "rating_text": "Three",
  "rating_stars": 3,
  "description": "It's hard to imagine a world without A Light in the Attic. ...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-09-12T16:30:04.915262+00:00"
}
```

`product_url` is each record's canonical identity — required, must be absolute `https://`.
`description` is the only field allowed to be `null` (some books may have no description; a missing
field is never invented — see `tests/test_extractor.py`).

A record that fails validation (bad URL, non-numeric price, etc.) never reaches `books.json` — it's
written to `output/errors.json` with the reason instead.

## Politeness rules I follow

| Rule | Where |
|---|---|
| Honest, identifying User-Agent on every real request | `config.USER_AGENT`, sent in `fetcher.fetch` |
| Timeout — a request must give up, never hang forever | `config.TIMEOUT_SECONDS` (8s) |
| ≥0.5s delay between real requests (never between cache hits) | `config.REQUEST_DELAY_SECONDS`, applied in `main.polite_fetch` |
| Status code checked before parsing anything | `fetcher.fetch` |
| On-disk cache — the site is asked once, then read from disk | `fetcher.fetch`, `cache/` |
| Retry on timeout / 429 / 5xx with real exponential backoff + jitter, honouring `Retry-After`; never retry 404/403 | `src/retry.py`, `fetcher.fetch` (see "retry like a pro" below) |

## Idempotency

Each run builds one fresh, de-duplicated list of valid records (keyed by `product_url`, the
canonical identity) and **overwrites** `books.json` with it — it never appends to the previous run's
file. That makes "run it twice, get 60 records, not 120" true by construction, with no merge logic
to get wrong (`storage.dedupe_by_url`).

## Tests

`pytest tests/` runs 25 tests. The five required cases:

1. **Price normalization** — `"£51.77"` → `51.77` (`test_normalizer.py`)
2. **Relative → absolute URLs** — resolved with `urljoin`, never string-gluing (`test_crawler.py`)
3. **Missing description** — stored as `null`, never invented (`test_extractor.py`)
4. **Duplicate URLs** — a repeated link on one page collapses to one unique URL (`test_crawler.py`)
5. **One malformed fixture** — a record with a bad price/URL is rejected with a reason, not silently
   accepted (`test_schema.py`)

Plus coverage for the extras: backoff math and `Retry-After` handling (`test_retry.py`), CSV
quoting (`test_csv_export.py`), change-detection hashing and diffing (`test_change_detection.py`),
the dashboard generator (`test_dashboard.py`), and the enrichment retry-on-bad-JSON path
(`test_enrich.py`, mocked so it runs without Ollama installed).

Fixtures in `tests/fixtures/` are built from the real DOM structure of the live sandbox — I fetched
the actual site (see Verification below) to get the real selectors and real text before writing the
extractor, rather than guessing.

## Extras (stretch/bonus, all implemented and verified)

| Extra | What it does | Where |
|---|---|---|
| **CSV export** | `output/books.csv` alongside the JSON | `src/csv_export.py` |
| **Change detection** | Hashes each record's content (not `fetched_at`) and reports new/changed/unchanged/gone vs. the previous run | `src/change_detection.py`, `output/change-report.json` |
| **Tiny dashboard** | One self-contained HTML file — record count, price range, failures, last-fresh time — no server, no CDN | `src/dashboard.py`, `output/dashboard.html` |
| **Retry like a pro** | Real exponential backoff + jitter, honours a `Retry-After` header, retries 429/5xx but never 404/403, structured JSON-line logs | `src/retry.py`, `src/logging_utils.py`, upgraded `src/fetcher.py`, `logs/scrape.jsonl` |
| **AI enrichment (local, via Ollama)** | Category + one-line summary per book, schema-forced with Pydantic, written to a file kept separate from scraped facts | `src/enrich.py` → `output/enrichment.json` |
| **Browser cost comparison** | Plain HTTP vs. Playwright on `quotes.toscrape.com/js`, timing + memory | `tools/browser_cost_compare.py` |
| **The AI rematch** | Full writeup, prompt, both generations, real bugs found and fixed | [`ai-version/AI_VS_ME.md`](ai-version/AI_VS_ME.md) |

All extras run automatically as part of `python -m src.main` (pass `--skip-extras` for the bare
7-stage pipeline). Enrichment and the browser comparison are separate commands since they need
extra local setup — see below.

```bash
# CSV, change-detection, and dashboard all happen automatically:
python -m src.main

# AI enrichment needs Ollama running locally first:
#   install: https://ollama.com
#   ollama pull llama3.2
python -m src.enrich

# Browser cost comparison needs Playwright's browser binary:
pip install playwright
playwright install chromium
python -m tools.browser_cost_compare
```

**Honest verification note on the two above:** I couldn't install Ollama or download a Playwright
browser binary from this dev sandbox (same network restriction as the main pipeline — see
Verification below). I verified `src/enrich.py`'s actual HTTP call, JSON parsing, and retry-on-
invalid-JSON logic against a real local server shaped like Ollama's API (including a deliberately
garbled first reply to prove the retry path fires), and I verified the browser-comparison's core
premise for real — fetching `https://quotes.toscrape.com/js` with plain HTTP returns zero quote
text, confirming the page really does need JavaScript. What I couldn't do here is run an actual
model or an actual browser — that's the one step that's genuinely yours to run.

## The AI rematch (bonus stage)

I did this one for real, not as a formality: wrote a prompt from memory, generated a fresh
implementation from only that prompt, then actually ran both versions against real test scenarios —
including a book with no description and a real mid-run price change — to see what broke. It found
three genuine bugs in the AI-generated version (a crash on missing descriptions, wasted retries on a
404, and a silent staleness bug where a rerun never picks up a price change), then one prompt
improvement fixed all three, verified again for real. Full writeup, both prompts, and both
generations are in [`ai-version/`](ai-version/).

## Why this assignment needed no browser

The book data (title, price, availability, description) is already present in the HTML the server
sends on first response — there's no JavaScript rendering step hiding it. A browser would only add
cost (memory, startup time) for zero extra data here.

## Verification (read this if the numbers below look small)

I built and tested this in a dev sandbox whose outbound network is restricted to a short allow-list
of package registries (pip/npm/GitHub) — `books.toscrape.com` isn't reachable directly from a
`requests.get()` in that sandbox. So instead of faking output, I did the following, for real:

1. Fetched `robots.txt` and all 3 real catalogue pages from the live site (confirming the 404
   robots result and getting the real list of 60 titles/prices/URLs).
2. Fetched 3 real book detail pages (including one non-English description, to check UTF-8
   handling) to get the exact real selectors — `div.product_main`, `#product_description`,
   `p.star-rating <Word>`, the info table — rather than guessing them.
3. Built `tests/fixtures/` from that real structure and real text, plus two deliberately-broken
   synthetic fixtures (missing description, extra whitespace) to exercise the edge cases.
4. Ran the **actual, unmodified** `src/fetcher.py` against a real local HTTP server to confirm the
   genuine `FETCH` → `CACHE HIT` behaviour, that a 404 is never retried, that a flaky endpoint
   returning `503, 503, 200` really does get three real attempts with real (measured) exponential
   backoff, and that a `429` with a `Retry-After: 1` header waits exactly 1 second instead of
   guessing.
5. Ran the **actual, unmodified** pipeline (`crawler` → `extractor` → `normalizer` → `schema` →
   `storage` → `report`) end-to-end against a 3-book local mirror of the real pages fetched in step 2,
   including a rerun (proving idempotency) and an injected broken URL (proving Stage 5). Only the
   transport was swapped for local files — the URLs, titles, prices, and descriptions in the result
   below are the real ones from the live site.
6. Verified the extras against that same mirror across three real runs: run 1 correctly reported all
   3 books as `new`; an immediate rerun correctly reported all 3 as `unchanged`; then I edited the
   mirror's HTML to drop one book's price and remove another entirely, reran, and change-detection
   correctly reported exactly `1 changed, 1 unchanged, 1 gone` — real values, not asserted ones.

Real `run-report.json` from that verification run (3-book mirror, one injected broken URL):

```json
{
  "started_at": "2026-09-12T16:29:20.890976+00:00",
  "ended_at": "2026-09-12T16:29:25.111108+00:00",
  "duration_seconds": 4.22,
  "catalogue_pages_fetched": 3,
  "book_pages_attempted": 4,
  "cache_hits": 0,
  "fetched_from_network": 7,
  "valid_records": 3,
  "invalid_records": 1,
  "failed_pages_count": 1,
  "failed_pages": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_00000/index.html",
      "reason": "HTTP 404"
    }
  ]
}
```

**`output/` is intentionally empty in this repo.** The next step is mine to do, not to fake: run
`python -m src.main` with normal internet access to get the real 60-record `books.json` and
`run-report.json`, then replace this section with that real report before submitting.

## Honest limitation

Ratings and prices on this sandbox are randomly assigned and reset periodically (the site says so
itself), so re-running weeks apart can show different `price_gbp` / `rating_stars` values for the
same book — that's the sandbox's behaviour, not a bug in this scraper. The `Retry-After` parsing in
`src/retry.py` also only handles a plain number of seconds, not an HTTP-date value — rare enough
for this API that I judged it not worth the timezone-parsing risk.

## Ethics note

I only scrape a site built for that purpose, and only the public data already present in the page
the server sends. I never bypass a login, a paywall, or a block — a 403 here means stop, not retry
harder. When a real API exists for a target, that's the right tool, not a scraper. I collect only
the fields this project actually needs.

## Not attempted

Background execution via a queued job (the A7-dependent stretch item) — I haven't done A7 yet, so
there's no job queue to plug this into. Everything else in Stage 6's extras and the "Done means"
stretch list is implemented above.
