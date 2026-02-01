"""TimeRange value object."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TimeRange:
    """Immutable value object representing a time range."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """Validate time range."""
        if self.start > self.end:
            raise ValueError("Start time must be before or equal to end time")

    @classmethod
    def last_hours(cls, hours: int) -> TimeRange:
        """Create time range for last N hours."""
        end = datetime.utcnow()
        start = end - timedelta(hours=hours)
        return cls(start=start, end=end)

    @classmethod
    def last_days(cls, days: int) -> TimeRange:
        """Create time range for last N days."""
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        return cls(start=start, end=end)

    @classmethod
    def last_weeks(cls, weeks: int) -> TimeRange:
        """Create time range for last N weeks."""
        return cls.last_days(weeks * 7)

    @classmethod
    def today(cls) -> TimeRange:
        """Create time range for today."""
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return cls(start=start, end=now)

    @classmethod
    def yesterday(cls) -> TimeRange:
        """Create time range for yesterday."""
        now = datetime.utcnow()
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=1)
        return cls(start=start, end=end)

    @property
    def duration(self) -> timedelta:
        """Get duration of time range."""
        return self.end - self.start

    @property
    def duration_hours(self) -> float:
        """Get duration in hours."""
        return self.duration.total_seconds() / 3600

    @property
    def duration_days(self) -> float:
        """Get duration in days."""
        return self.duration.total_seconds() / 86400

    def contains(self, dt: datetime) -> bool:
        """Check if datetime falls within range."""
        return self.start <= dt <= self.end

    def overlaps(self, other: TimeRange) -> bool:
        """Check if this range overlaps with another."""
        return self.start <= other.end and self.end >= other.start

    def split_by_days(self) -> list[TimeRange]:
        """Split time range into daily ranges."""
        ranges = []
        current_start = self.start

        while current_start < self.end:
            # End of current day
            next_day = (current_start + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            current_end = min(next_day, self.end)
            ranges.append(TimeRange(start=current_start, end=current_end))
            current_start = next_day

        return ranges
