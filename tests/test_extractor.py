from src.extractor import extract_raw_record

PRODUCT_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
SOURCE_PAGE = "https://books.toscrape.com/catalogue/page-1.html"
FETCHED_AT = "2026-09-12T10:00:00+00:00"


def test_extract_normal_book_gets_all_eight_fields(load_fixture):
    html = load_fixture("book_normal.html")
    record = extract_raw_record(html, PRODUCT_URL, SOURCE_PAGE, FETCHED_AT)

    assert record["title"] == "A Light in the Attic"
    assert record["price_text"] == "£51.77"
    assert record["availability_text"] == "In stock (22 available)"
    assert record["rating_text"] == "Three"
    assert record["description"].startswith("It's hard to imagine a world")
    assert record["product_url"] == PRODUCT_URL
    assert record["source_page"] == SOURCE_PAGE
    assert record["fetched_at"] == FETCHED_AT
    assert set(record.keys()) == {
        "title", "product_url", "price_text", "availability_text",
        "rating_text", "description", "source_page", "fetched_at",
    }


def test_missing_description_is_stored_as_none_not_invented(load_fixture):
    html = load_fixture("book_no_description.html")
    record = extract_raw_record(html, PRODUCT_URL, SOURCE_PAGE, FETCHED_AT)

    assert record["title"] == "Untitled Fixture Book"
    assert record["description"] is None  # never invent text that wasn't on the page


def test_extra_whitespace_is_collapsed(load_fixture):
    html = load_fixture("book_extra_whitespace.html")
    record = extract_raw_record(html, PRODUCT_URL, SOURCE_PAGE, FETCHED_AT)

    assert record["title"] == "Tipping the Velvet"
    assert record["price_text"] == "£53.74"
    assert record["availability_text"] == "In stock (20 available)"
    assert "  " not in record["description"]  # no doubled-up internal whitespace
