from src.normalizer import parse_availability, parse_price_gbp, rating_to_stars


def test_parse_price_gbp_turns_currency_text_into_a_float():
    assert parse_price_gbp("£51.77") == 51.77
    assert parse_price_gbp("£9.00") == 9.00
    assert parse_price_gbp(None) is None
    assert parse_price_gbp("") is None


def test_parse_availability_extracts_count_and_in_stock_flag():
    assert parse_availability("In stock (22 available)") == (True, 22)
    assert parse_availability("In stock") == (True, None)
    assert parse_availability("Out of stock") == (False, None)
    assert parse_availability(None) == (False, None)


def test_rating_word_maps_to_a_number_and_unknown_words_are_none():
    assert rating_to_stars("Three") == 3
    assert rating_to_stars("Five") == 5
    assert rating_to_stars("Zero") == 0
    assert rating_to_stars("Bogus") is None
    assert rating_to_stars(None) is None
