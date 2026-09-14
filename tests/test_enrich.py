import json
from unittest.mock import patch, MagicMock

from src.enrich import enrich_one


def _fake_response(text: str):
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"response": text}
    return mock


def test_valid_json_on_first_try_is_accepted():
    good = json.dumps({"category": "Poetry", "summary": "A short poetry collection."})
    with patch("src.enrich.requests.post", return_value=_fake_response(good)) as mock_post:
        result = enrich_one("https://example.com/book/1", "Some Book", "A description.")

    assert result is not None
    assert result.category == "Poetry"
    assert mock_post.call_count == 1


def test_invalid_json_is_retried_once_then_accepted():
    bad = "not json at all"
    good = json.dumps({"category": "Fiction", "summary": "A novel about something."})
    with patch("src.enrich.requests.post", side_effect=[_fake_response(bad), _fake_response(good)]) as mock_post:
        result = enrich_one("https://example.com/book/2", "Some Novel", "A description.")

    assert result is not None
    assert result.category == "Fiction"
    assert mock_post.call_count == 2


def test_still_invalid_after_retry_returns_none_not_a_guess():
    bad = "not json at all"
    with patch("src.enrich.requests.post", return_value=_fake_response(bad)):
        result = enrich_one("https://example.com/book/3", "Some Book", "A description.")

    assert result is None
