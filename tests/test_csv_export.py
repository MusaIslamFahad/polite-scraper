import csv
from pathlib import Path

from src.csv_export import write_csv
from src.schema import BookRecord

RECORD = BookRecord(
    title="A Light in the Attic",
    product_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    price_text="£51.77",
    price_gbp=51.77,
    availability_text="In stock (22 available)",
    availability_count=22,
    in_stock=True,
    rating_text="Three",
    rating_stars=3,
    description="A description, with a comma in it.",
    source_page="https://books.toscrape.com/catalogue/page-1.html",
    fetched_at="2026-09-12T10:00:00+00:00",
)


def test_csv_has_one_row_per_record_and_the_right_columns(tmp_path: Path):
    out = tmp_path / "books.csv"
    count = write_csv([RECORD], out)

    assert count == 1
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["title"] == "A Light in the Attic"
    assert rows[0]["price_gbp"] == "51.77"


def test_a_comma_inside_description_does_not_break_the_csv(tmp_path: Path):
    # This is the one field that actually needs CSV-safe quoting.
    out = tmp_path / "books.csv"
    write_csv([RECORD], out)

    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert rows[0]["description"] == "A description, with a comma in it."
