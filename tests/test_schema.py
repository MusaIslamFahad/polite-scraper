from src.schema import validate_record

VALID = {
    "title": "A Light in the Attic",
    "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "price_text": "£51.77",
    "price_gbp": 51.77,
    "availability_text": "In stock (22 available)",
    "availability_count": 22,
    "in_stock": True,
    "rating_text": "Three",
    "rating_stars": 3,
    "description": "It's hard to imagine a world without A Light in the Attic.",
    "source_page": "https://books.toscrape.com/catalogue/page-1.html",
    "fetched_at": "2026-09-12T10:00:00+00:00",
}


def test_a_valid_record_passes_and_has_no_error():
    record, reason = validate_record(VALID)
    assert record is not None
    assert reason is None
    assert record.price_gbp == 51.77


def test_a_malformed_record_is_rejected_with_a_reason():
    # Two things wrong at once: price could not be parsed (0, not > 0)
    # and the URL is relative instead of absolute — either alone should fail.
    broken = {**VALID, "price_gbp": 0, "product_url": "catalogue/no-such-book/index.html"}

    record, reason = validate_record(broken)

    assert record is None
    assert reason is not None
    assert len(reason) > 0
