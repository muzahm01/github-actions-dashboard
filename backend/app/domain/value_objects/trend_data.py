"""Trend data value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class TrendDirection(str, Enum):
    """Direction of trend."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class TrendPeriod(str, Enum):
    """Period for trend aggregation."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


MetricType = Literal[
    "total_runs",
    "success_rate",
    "failure_rate",
    "avg_duration",
    "total_failures",
]


@dataclass(frozen=True)
class TrendPoint:
    """Single data point in a trend."""

    timestamp: datetime
    value: float
    count: int = 0  # Number of samples for this point
    metadata: dict = field(default_factory=dict)

    @classmethod
    def zero(cls, timestamp: datetime) -> TrendPoint:
        """Create zero value point."""
        return cls(timestamp=timestamp, value=0.0, count=0)

    def __add__(self, other: TrendPoint) -> TrendPoint:
        """Add two trend points (for aggregation)."""
        return TrendPoint(
            timestamp=self.timestamp,
            value=self.value + other.value,
            count=self.count + other.count,
        )


@dataclass(frozen=True)
class TrendData:
    """Trend data for a metric over time."""

    metric_type: MetricType
    period: TrendPeriod
    points: tuple[TrendPoint, ...]
    start_date: datetime
    end_date: datetime

    @property
    def direction(self) -> TrendDirection:
        """Determine trend direction."""
        if len(self.points) < 2:
            return TrendDirection.STABLE

        # Compare first and last third averages
        third = max(1, len(self.points) // 3)
        first_avg = sum(p.value for p in self.points[:third]) / third
        last_avg = sum(p.value for p in self.points[-third:]) / third

        threshold = 0.05  # 5% change threshold
        if last_avg > first_avg * (1 + threshold):
            return TrendDirection.UP
        elif last_avg < first_avg * (1 - threshold):
            return TrendDirection.DOWN
        return TrendDirection.STABLE

    @property
    def average(self) -> float:
        """Calculate average value."""
        if not self.points:
            return 0.0
        return sum(p.value for p in self.points) / len(self.points)

    @property
    def minimum(self) -> float:
        """Get minimum value."""
        if not self.points:
            return 0.0
        return min(p.value for p in self.points)

    @property
    def maximum(self) -> float:
        """Get maximum value."""
        if not self.points:
            return 0.0
        return max(p.value for p in self.points)

    @property
    def total(self) -> float:
        """Get total/sum of values."""
        return sum(p.value for p in self.points)

    @property
    def change_percent(self) -> float:
        """Calculate percentage change from start to end."""
        if len(self.points) < 2:
            return 0.0
        first = self.points[0].value
        last = self.points[-1].value
        if first == 0:
            return 0.0 if last == 0 else 100.0
        return ((last - first) / first) * 100

    def is_improving(self) -> bool:
        """Check if trend is improving (depends on metric type)."""
        # For success_rate, up is good. For failure_rate, down is good.
        if self.metric_type in ("success_rate",):
            return self.direction == TrendDirection.UP
        elif self.metric_type in ("failure_rate", "total_failures"):
            return self.direction == TrendDirection.DOWN
        return self.direction == TrendDirection.STABLE


@dataclass(frozen=True)
class TrendSummary:
    """Summary of trends across multiple metrics."""

    total_runs: int
    success_rate: float
    failure_rate: float
    avg_duration_seconds: float
    success_rate_trend: TrendDirection
    failure_trend: TrendDirection
    top_failing_workflows: tuple[dict, ...] = field(default_factory=tuple)
    comparison_period: str = ""  # e.g., "vs last week"
    success_rate_change: float = 0.0
