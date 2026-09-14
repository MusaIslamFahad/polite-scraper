# AI vs me

The bonus stage, done for real: I wrote a prompt from memory (not from the assignment PDF),
generated `scraper.py` from it alone, then actually ran both that version and my hand-built `src/`
pipeline against the same checkpoints. Everything below is a real result, not a guess at what
"probably" would happen — see `PROMPT.md`, `scraper.py`, `PROMPT_V2.md`, and `scraper_v2.py` in this
folder for the actual artifacts.

## The prompt

See [`PROMPT.md`](PROMPT.md) for the exact wording. Short version: I described the 7-stage goal
from memory — target, fields, politeness, validation, don't-crash-on-a-bad-page, don't-duplicate-
on-rerun, and a run summary — without re-reading the assignment's specific edge-case call-outs
(missing descriptions, which status codes to retry, the "raw and clean side by side" schema rule).

## Checkpoint results

| Checkpoint | My hand-built `src/` | AI-generated `scraper.py` (v1) |
|---|---|---|
| Collects all 60 book pages, 3 catalogue pages only | ✅ | ✅ |
| Reruns without duplicating | ✅ (full rebuild, keyed by URL) | ✅ (append-if-new-URL) |
| Survives one broken (404) page | ✅ skips immediately, no wasted retry | ⚠️ "survives" but retries the 404 3 times anyway — wastes ~3s per broken page for no benefit |
| Survives a book with no description | ✅ stores `null` | ❌ **crashes the entire run** — `AttributeError: 'NoneType' object has no attribute 'find_next_sibling'` |
| A rerun picks up a real content change (price, rating) | ✅ overwrites fresh every run | ❌ **silently stale** — once a URL is in the file, it's never re-scraped or updated, ever |
| Raw text kept alongside the parsed value (`price_text` + `price_gbp`) | ✅ | ❌ only stores the parsed number, the original `"£51.77"` is thrown away |
| Structured run report | ✅ `run-report.json` with cache hits, timing, failed-page reasons | ⚠️ a report exists, but thinner (no timing, no cache-hit count) |

Rows marked ✅/❌ above aren't estimates — I reproduced every one of them by pointing both scripts
at the same local mirror of real scraped pages (the same one described in the main README's
Verification section) and reading the actual output. The exact commands and console output are in
`verify_ai_version.py` (paraphrased below, not pasted verbatim to keep this file short):

```
Scenario: one book has no #product_description block
  -> CRASHED as predicted: AttributeError: 'NoneType' object has no attribute 'find_next_sibling'

Scenario: one deliberately broken (404) URL — does it waste retries?
  -> Got status 404 ... retrying...   (x3)
  -> Total run time with one 404 in the list: 8.0s

Scenario: does a rerun pick up a real price change?
  -> Price on first run: £51.77
  -> Price on second run (site now shows £45.00): £51.77
  -> STALE — the rerun never updated it!
```

## Three concrete differences (there are more above, but per the checkpoint's ask, here are three)

1. **Error handling scope.** My prompt said "don't let a bad page crash the whole run" — and the AI
   version's network-fetch code does honor that. But the *parsing* step has no equivalent guard, so
   a page that loads fine (200) but has an unexpected shape (no description block) takes down the
   entire process. My prompt was fetch-specific; I never said "and the parsing step too." That's a
   gap in what I asked for, not just in what the AI produced.

2. **Retry policy.** I said "don't crash on a failed page," which the AI reasonably read as "retry
   failures." But I never distinguished *which* failures are worth retrying. The assignment PDF
   explicitly calls out 404-never-retries / 403-never-retries — a detail I knew when I built `src/`
   by hand, but didn't think to repeat in a from-memory prompt months later.

3. **Idempotency vs freshness.** "Don't duplicate on rerun" and "keep the data fresh" sound like the
   same requirement but aren't. A pure append-if-new-URL check satisfies the first without
   satisfying the second — and it's the kind of bug that never throws an error or looks wrong, it
   just quietly stops being true. I only noticed because I deliberately changed a price and reran.

## What my prompt forgot to say

Reading the gaps backwards, my from-memory prompt was missing exactly the things that live in the
assignment's Glossary and edge-case notes, not the main flow: retryable vs non-retryable status
codes, "some books may have no description," and "keep raw and clean values side by side." I
remembered the shape of the pipeline; I forgot the specific scars from the PDF's specific warnings.

## One rematch

New prompt: [`PROMPT_V2.md`](PROMPT_V2.md) — same as v1, plus the four fixes above stated explicitly.
New generation: [`scraper_v2.py`](scraper_v2.py) (not hand-patched from v1 — a fresh generation from
the improved prompt). Re-ran the same three failing scenarios against it:

```
Scenario: missing description (should NOT crash now)
  -> Did NOT crash. description field = None

Scenario: 404 should NOT be retried
  -> Got 404 ... — not retrying, that won't change.
  -> Total run time with one 404 in the list: 5.0s   (was 8.0s)

Scenario: does a rerun pick up a real price change now?
  -> Price on first run: £51.77
  -> Price on second run (site now shows £45.00): £45.0
  -> Updated correctly!
```

All three fixed, for real, on the first regeneration from the improved prompt. Still missing versus
`src/` even after the rematch: raw+clean side-by-side price fields, structured logs, exponential
backoff (v2 still waits a flat `DELAY` between retries), CSV/dashboard/change-detection, and a real
test suite. A better prompt fixed exactly what it was told to fix — it didn't spontaneously reach
for anything beyond that. Which is really the whole lesson of this stage: the spec quality is the
ceiling, and only actually running the thing tells you where the floor is.
