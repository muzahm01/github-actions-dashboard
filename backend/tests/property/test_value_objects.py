"""Property-based tests for domain value objects using Hypothesis."""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.value_objects.pagination import PaginatedResult, Pagination
from app.domain.value_objects.search_query import SearchQuery, SearchResult, SearchType
from app.domain.value_objects.time_range import TimeRange

pytestmark = pytest.mark.unit


# --- Pagination ---


@given(page=st.integers(), per_page=st.integers(), max_per_page=st.integers(min_value=1))
@settings(max_examples=100)
def test_pagination_always_valid(page: int, per_page: int, max_per_page: int) -> None:
    """Pagination always clamps to valid values regardless of input."""
    p = Pagination(page=page, per_page=per_page, max_per_page=max_per_page)
    assert p.page >= 1
    assert 1 <= p.per_page <= p.max_per_page
    assert p.offset >= 0
    assert p.limit >= 1


@given(page=st.integers(min_value=1, max_value=10000), per_page=st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_pagination_offset_is_monotonic(page: int, per_page: int) -> None:
    """Larger page numbers always produce larger offsets."""
    p1 = Pagination(page=page, per_page=per_page)
    p2 = Pagination(page=page + 1, per_page=per_page)
    assert p2.offset > p1.offset


@given(page=st.integers(min_value=2, max_value=10000), per_page=st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_pagination_next_prev_roundtrip(page: int, per_page: int) -> None:
    """next_page().prev_page() returns to the original page."""
    p = Pagination(page=page, per_page=per_page)
    assert p.next_page().prev_page().page == p.page


@given(
    items=st.lists(st.integers(), min_size=0, max_size=20),
    total=st.integers(min_value=0, max_value=1000),
    page=st.integers(min_value=1, max_value=100),
    per_page=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=100)
def test_paginated_result_properties(
    items: list[int], total: int, page: int, per_page: int
) -> None:
    """PaginatedResult properties are always consistent."""
    r = PaginatedResult(items=items, total=total, page=page, per_page=per_page)
    assert r.total_pages >= 0
    assert r.is_empty == (len(items) == 0)
    if r.total_pages > 0:
        assert r.has_next == (page < r.total_pages)
    assert r.has_prev == (page > 1)


# --- TimeRange ---


@given(
    start=st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 1, 1)),
    duration=st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=365)),
)
@settings(max_examples=100)
def test_time_range_duration_non_negative(start: datetime, duration: timedelta) -> None:
    """TimeRange duration is always non-negative."""
    end = start + duration
    tr = TimeRange(start=start, end=end)
    assert tr.duration >= timedelta(0)
    assert tr.duration_hours >= 0
    assert tr.duration_days >= 0


@given(
    start=st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 1, 1)),
    duration=st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=365)),
)
@settings(max_examples=50)
def test_time_range_contains_boundaries(start: datetime, duration: timedelta) -> None:
    """TimeRange always contains its own start and end."""
    end = start + duration
    tr = TimeRange(start=start, end=end)
    assert tr.contains(start)
    assert tr.contains(end)


@given(
    start=st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 1, 1)),
    duration=st.timedeltas(min_value=timedelta(hours=1), max_value=timedelta(days=10)),
)
@settings(max_examples=50)
def test_time_range_split_covers_entire_range(start: datetime, duration: timedelta) -> None:
    """split_by_days covers the entire original range."""
    end = start + duration
    tr = TimeRange(start=start, end=end)
    parts = tr.split_by_days()

    assert len(parts) >= 1
    assert parts[0].start == tr.start
    assert parts[-1].end == tr.end

    # Parts are contiguous
    for i in range(len(parts) - 1):
        assert parts[i].end == parts[i + 1].start


@given(
    start=st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 1, 1)),
    duration=st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=365)),
)
@settings(max_examples=50)
def test_time_range_overlaps_itself(start: datetime, duration: timedelta) -> None:
    """A TimeRange always overlaps with itself."""
    end = start + duration
    tr = TimeRange(start=start, end=end)
    assert tr.overlaps(tr)


# --- SearchQuery ---


@given(
    limit=st.integers(),
    min_score=st.floats(allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_search_query_always_clamped(limit: int, min_score: float) -> None:
    """SearchQuery always clamps limit and min_score to valid ranges."""
    q = SearchQuery(query="test", limit=limit, min_score=min_score)
    assert 1 <= q.limit <= 100
    assert 0.0 <= q.min_score <= 1.0


@given(
    score=st.floats(min_value=0.0, max_value=1.0),
    threshold=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=100)
def test_search_result_is_relevant_consistent(score: float, threshold: float) -> None:
    """is_relevant returns True iff score >= threshold."""
    r = SearchResult(id=1, result_type="log", title="t", score=score)
    assert r.is_relevant(threshold) == (score >= threshold)
