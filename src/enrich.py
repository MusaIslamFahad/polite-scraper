"""
Stretch — AI enrichment, locally, via Ollama.

Run separately from the main pipeline, on purpose:

    python -m src.enrich

It reads the already-validated output/books.json, asks a local model for a
one-word-ish category and a short summary of each description, forces the
reply through a schema, and writes output/enrichment.json — a SEPARATE
file, never merged back into books.json. The model's opinion about a book
is not a scraped fact, and this project keeps that line bright.

Requires Ollama running locally with a model pulled, e.g.:
    ollama pull llama3.2
    ollama serve   # usually already running as a background service

This talks to Ollama's HTTP API directly (no SDK) so there's exactly one
new dependency surface to reason about: `requests`, which the project
already uses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import requests
from pydantic import BaseModel, ValidationError

from . import config

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
ENRICHMENT_JSON = config.OUTPUT_DIR / "enrichment.json"

PROMPT_TEMPLATE = """You are labelling a book catalogue entry. Read the title and description below \
and respond with ONLY a JSON object with exactly two keys:
  "category": one or two words for the book's genre/topic, guessed from the text
  "summary": a single plain sentence (max 25 words) summarising the description

Title: {title}
Description: {description}

Respond with JSON only, no other text."""


class Enrichment(BaseModel):
    product_url: str
    category: str
    summary: str


def _call_ollama(prompt: str, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_URL, timeout: int = 30) -> str:
    resp = requests.post(
        base_url,
        json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def enrich_one(product_url: str, title: str, description: str,
                model: str = OLLAMA_MODEL, base_url: str = OLLAMA_URL,
                max_attempts: int = 2) -> Optional[Enrichment]:
    """
    Ask the model once, and if it doesn't return valid JSON matching the
    schema, ask exactly once more with a stricter reminder before giving up.
    A record we can't enrich is skipped, not invented.
    """
    prompt = PROMPT_TEMPLATE.format(title=title, description=description)

    for attempt in range(1, max_attempts + 1):
        try:
            raw = _call_ollama(prompt, model=model, base_url=base_url)
            parsed = json.loads(raw)
            return Enrichment(product_url=product_url, **parsed)
        except (requests.exceptions.RequestException, json.JSONDecodeError, ValidationError, KeyError, TypeError) as exc:
            if attempt == max_attempts:
                print(f"ENRICH FAILED {product_url}: {exc}")
                return None
            prompt = PROMPT_TEMPLATE.format(title=title, description=description) + \
                "\nYour previous reply was not valid JSON with exactly those two keys. Try again."

    return None


def enrich_book_records(records: List[dict], model: str = OLLAMA_MODEL, base_url: str = OLLAMA_URL) -> List[Enrichment]:
    results = []
    for record in records:
        description = record.get("description")
        if not description:
            continue  # nothing to summarise — don't invent an opinion about text that isn't there
        result = enrich_one(record["product_url"], record["title"], description, model=model, base_url=base_url)
        if result:
            results.append(result)
    return results


def main() -> None:
    if not config.BOOKS_JSON.exists():
        print("output/books.json not found — run `python -m src.main` first.")
        return

    records = json.loads(config.BOOKS_JSON.read_text(encoding="utf-8"))

    try:
        results = enrich_book_records(records)
    except requests.exceptions.ConnectionError:
        print(
            "Could not reach Ollama at http://localhost:11434 — is it running?\n"
            "Install: https://ollama.com  |  Start a model: `ollama pull llama3.2`"
        )
        return

    ENRICHMENT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ENRICHMENT_JSON.write_text(
        json.dumps([r.model_dump() for r in results], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"enrichment.json: {len(results)}/{len(records)} records enriched")


if __name__ == "__main__":
    main()
