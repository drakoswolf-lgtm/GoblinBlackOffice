from collections import defaultdict
import random

from app.office.loading_sticky import (
    LOAD_BEARING_STICKY_LINES,
    choose_sticky_line,
    sticky_candidates,
)


def test_production_pool_has_exactly_24_lines():
    assert len(LOAD_BEARING_STICKY_LINES) == 24
    assert len({line.key for line in LOAD_BEARING_STICKY_LINES}) == 24


def test_progress_bands_cover_zero_through_99_without_overlap():
    for progress in range(100):
        candidates = sticky_candidates(progress)
        assert len(candidates) == 6
        ranges = {(line.min_progress, line.max_progress) for line in candidates}
        assert len(ranges) == 1


def test_each_progress_band_weights_sum_to_100():
    totals = defaultdict(int)
    for line in LOAD_BEARING_STICKY_LINES:
        totals[(line.min_progress, line.max_progress)] += line.weight
    assert totals == {
        (0, 24): 100,
        (25, 49): 100,
        (50, 79): 100,
        (80, 99): 100,
    }


def test_100_percent_returns_no_joke_because_explosion_should_start():
    assert sticky_candidates(100) == ()
    assert choose_sticky_line(100) is None


def test_selection_is_seedable_for_ui_tests():
    first = choose_sticky_line(30, rng=random.Random(7))
    second = choose_sticky_line(30, rng=random.Random(7))
    assert first == second
    assert first in sticky_candidates(30)
