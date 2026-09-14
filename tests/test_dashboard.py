from src.dashboard import build_dashboard_html
from src.schema import BookRecord

RECORD = BookRecord(
    title="A Light in the Attic",
    product_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    price_text="£51.77", price_gbp=51.77,
    availability_text="In stock (22 available)", availability_count=22, in_stock=True,
    rating_text="Three", rating_stars=3,
    description="Some description.",
    source_page="https://books.toscrape.com/catalogue/page-1.html",
    fetched_at="2026-09-12T10:00:00+00:00",
)
REPORT = {"failed_pages_count": 0}


def test_dashboard_is_self_contained_and_shows_the_real_numbers():
    html = build_dashboard_html([RECORD], REPORT, generated_at="2026-09-12T10:05:00+00:00")

    assert "<html" in html
    assert "A Light in the Attic" in html
    assert "£51.77" in html
    assert "src=\"http" not in html  # no external script/CDN dependency
    assert "cdn." not in html


def test_dashboard_handles_zero_records_without_crashing():
    html = build_dashboard_html([], REPORT, generated_at="2026-09-12T10:05:00+00:00")
    assert "No records yet" in html
