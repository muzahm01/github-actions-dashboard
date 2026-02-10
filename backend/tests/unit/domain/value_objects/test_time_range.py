"""Tests for TimeRange value object."""

from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from app.domain.value_objects.time_range import TimeRange


class TestTimeRange:
    """Tests for the TimeRange value object."""

    @pytest.mark.unit
    def test_valid_range(self) -> None:
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 2)
        tr = TimeRange(start=start, end=end)
        assert tr.start == start
        assert tr.end == end

    @pytest.mark.unit
    def test_same_start_end(self) -> None:
        dt = datetime(2024, 1, 1)
        tr = TimeRange(start=dt, end=dt)
        assert tr.duration == timedelta(0)

    @pytest.mark.unit
    def test_invalid_range_raises(self) -> None:
        with pytest.raises(ValueError, match="Start time must be before"):
            TimeRange(start=datetime(2024, 1, 2), end=datetime(2024, 1, 1))

    @pytest.mark.unit
    def test_duration(self) -> None:
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 3))
        assert tr.duration == timedelta(days=2)

    @pytest.mark.unit
    def test_duration_hours(self) -> None:
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 2))
        assert tr.duration_hours == 24.0

    @pytest.mark.unit
    def test_duration_days(self) -> None:
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 4))
        assert tr.duration_days == 3.0

    @pytest.mark.unit
    def test_contains_inside(self) -> None:
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 31))
        assert tr.contains(datetime(2024, 1, 15)) is True

    @pytest.mark.unit
    def test_contains_boundary(self) -> None:
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 31))
        assert tr.contains(datetime(2024, 1, 1)) is True
        assert tr.contains(datetime(2024, 1, 31)) is True

    @pytest.mark.unit
    def test_contains_outside(self) -> None:
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 31))
        assert tr.contains(datetime(2023, 12, 31)) is False
        assert tr.contains(datetime(2024, 2, 1)) is False

    @pytest.mark.unit
    def test_overlaps_true(self) -> None:
        tr1 = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 15))
        tr2 = TimeRange(start=datetime(2024, 1, 10), end=datetime(2024, 1, 20))
        assert tr1.overlaps(tr2) is True
        assert tr2.overlaps(tr1) is True

    @pytest.mark.unit
    def test_overlaps_adjacent(self) -> None:
        tr1 = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 10))
        tr2 = TimeRange(start=datetime(2024, 1, 10), end=datetime(2024, 1, 20))
        assert tr1.overlaps(tr2) is True

    @pytest.mark.unit
    def test_overlaps_false(self) -> None:
        tr1 = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 5))
        tr2 = TimeRange(start=datetime(2024, 1, 10), end=datetime(2024, 1, 20))
        assert tr1.overlaps(tr2) is False

    @pytest.mark.unit
    def test_split_by_days_single_day(self) -> None:
        tr = TimeRange(
            start=datetime(2024, 1, 1, 10, 0),
            end=datetime(2024, 1, 1, 18, 0),
        )
        parts = tr.split_by_days()
        assert len(parts) == 1
        assert parts[0].start == datetime(2024, 1, 1, 10, 0)
        assert parts[0].end == datetime(2024, 1, 1, 18, 0)

    @pytest.mark.unit
    def test_split_by_days_multi_day(self) -> None:
        tr = TimeRange(
            start=datetime(2024, 1, 1, 10, 0),
            end=datetime(2024, 1, 3, 6, 0),
        )
        parts = tr.split_by_days()
        assert len(parts) == 3
        assert parts[0].start == datetime(2024, 1, 1, 10, 0)
        assert parts[0].end == datetime(2024, 1, 2, 0, 0)
        assert parts[1].start == datetime(2024, 1, 2, 0, 0)
        assert parts[1].end == datetime(2024, 1, 3, 0, 0)
        assert parts[2].start == datetime(2024, 1, 3, 0, 0)
        assert parts[2].end == datetime(2024, 1, 3, 6, 0)

    @pytest.mark.unit
    @freeze_time("2024-06-15 12:00:00")
    def test_last_hours(self) -> None:
        tr = TimeRange.last_hours(6)
        assert tr.end == datetime(2024, 6, 15, 12, 0, 0)
        assert tr.start == datetime(2024, 6, 15, 6, 0, 0)

    @pytest.mark.unit
    @freeze_time("2024-06-15 12:00:00")
    def test_last_days(self) -> None:
        tr = TimeRange.last_days(3)
        assert tr.end == datetime(2024, 6, 15, 12, 0, 0)
        assert tr.start == datetime(2024, 6, 12, 12, 0, 0)

    @pytest.mark.unit
    @freeze_time("2024-06-15 12:00:00")
    def test_last_weeks(self) -> None:
        tr = TimeRange.last_weeks(2)
        assert tr.duration_days == 14.0

    @pytest.mark.unit
    @freeze_time("2024-06-15 12:00:00")
    def test_today(self) -> None:
        tr = TimeRange.today()
        assert tr.start == datetime(2024, 6, 15, 0, 0, 0)
        assert tr.end == datetime(2024, 6, 15, 12, 0, 0)

    @pytest.mark.unit
    @freeze_time("2024-06-15 12:00:00")
    def test_yesterday(self) -> None:
        tr = TimeRange.yesterday()
        assert tr.start == datetime(2024, 6, 14, 0, 0, 0)
        assert tr.end == datetime(2024, 6, 15, 0, 0, 0)

    @pytest.mark.unit
    def test_frozen(self) -> None:
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 1, 2))
        with pytest.raises(AttributeError):
            tr.start = datetime(2024, 1, 5)  # type: ignore[misc]
