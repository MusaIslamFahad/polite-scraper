import random

from src.retry import compute_backoff_seconds, parse_retry_after


def test_retry_after_header_is_obeyed_exactly_when_present():
    assert parse_retry_after("5") == 5.0
    assert parse_retry_after(None) is None
    assert parse_retry_after("not-a-number") is None  # falls back to backoff, doesn't crash


def test_backoff_grows_exponentially_without_a_retry_after_header():
    rng = random.Random(0)  # deterministic jitter for a reproducible test
    wait_1 = compute_backoff_seconds(1, base_seconds=1.0, jitter_fraction=0, rng=rng)
    wait_2 = compute_backoff_seconds(2, base_seconds=1.0, jitter_fraction=0, rng=rng)
    wait_3 = compute_backoff_seconds(3, base_seconds=1.0, jitter_fraction=0, rng=rng)

    assert wait_1 == 1.0
    assert wait_2 == 2.0
    assert wait_3 == 4.0


def test_backoff_is_capped_so_it_never_waits_forever():
    wait = compute_backoff_seconds(10, base_seconds=1.0, cap_seconds=30.0, jitter_fraction=0)
    assert wait == 30.0


def test_retry_after_header_wins_over_computed_backoff():
    wait = compute_backoff_seconds(1, retry_after_header="12", base_seconds=1.0)
    assert wait == 12.0
