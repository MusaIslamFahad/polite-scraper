from src.crawler import parse_catalogue_page

PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"


def test_relative_links_become_absolute_urls(load_fixture):
    html = load_fixture("catalogue_page_sample.html")
    book_urls, _ = parse_catalogue_page(html, PAGE_URL)

    for url in book_urls:
        assert url.startswith("https://books.toscrape.com/catalogue/")


def test_next_link_is_resolved_relative_to_the_page(load_fixture):
    html = load_fixture("catalogue_page_sample.html")
    _, next_url = parse_catalogue_page(html, PAGE_URL)

    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_duplicate_product_links_on_one_page_are_still_returned_in_order(load_fixture):
    # parse_catalogue_page itself returns raw hits (3, including the repeat);
    # de-duplication happens one level up in crawler.discover(). This test
    # locks in that behaviour so a future refactor can't silently move the
    # dedup point without a test noticing.
    html = load_fixture("catalogue_page_sample.html")
    book_urls, _ = parse_catalogue_page(html, PAGE_URL)

    assert len(book_urls) == 3
    assert len(set(book_urls)) == 2  # the repeat collapses to 1 unique URL
