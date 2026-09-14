from src.change_detection import compute_hashes, diff_against_previous
from src.schema import BookRecord

BASE = dict(
    title="A Light in the Attic",
    product_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    price_text="£51.77", price_gbp=51.77,
    availability_text="In stock (22 available)", availability_count=22, in_stock=True,
    rating_text="Three", rating_stars=3,
    description="Some description.",
    source_page="https://books.toscrape.com/catalogue/page-1.html",
    fetched_at="2026-09-12T10:00:00+00:00",
)


def test_identical_content_hashes_the_same_even_with_a_different_fetched_at():
    r1 = BookRecord(**BASE)
    r2 = BookRecord(**{**BASE, "fetched_at": "2026-09-13T09:00:00+00:00"})

    hashes = compute_hashes([r1])
    hashes2 = compute_hashes([r2])
    assert hashes[r1.product_url] == hashes2[r2.product_url]


def test_a_real_content_change_produces_a_different_hash():
    r1 = BookRecord(**BASE)
    r2 = BookRecord(**{**BASE, "price_gbp": 45.00, "price_text": "£45.00"})

    hashes1 = compute_hashes([r1])
    hashes2 = compute_hashes([r2])
    assert hashes1[r1.product_url] != hashes2[r2.product_url]


def test_diff_classifies_new_changed_unchanged_and_gone():
    previous = {"url-a": "hash-a", "url-b": "hash-b"}
    current = {"url-a": "hash-a", "url-b": "hash-b-changed", "url-c": "hash-c"}

    diff = diff_against_previous(current, previous)

    assert diff["new"] == 1 and diff["new_urls"] == ["url-c"]
    assert diff["changed"] == 1 and diff["changed_urls"] == ["url-b"]
    assert diff["unchanged"] == 1
    assert diff["gone"] == 0
