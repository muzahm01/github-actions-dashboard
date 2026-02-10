"""Trend analysis and reporting API endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class TrendPeriod(str, Enum):
    """Period for trend aggregation."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TrendDirection(str, Enum):
    """Direction of trend."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class TrendPointResponse(BaseModel):
    """Single data point in a trend."""

    timestamp: datetime
    value: float
    count: int = 0


class TrendDataResponse(BaseModel):
    """Trend data for a metric."""

    metric_type: str
    period: TrendPeriod
    points: list[TrendPointResponse]
    start_date: datetime
    end_date: datetime
    direction: TrendDirection
    average: float
    minimum: float
    maximum: float
    total: float
    change_percent: float


class SuccessRateTrendResponse(BaseModel):
    """Success rate trend over time."""

    period: TrendPeriod
    points: list[TrendPointResponse]
    start_date: datetime
    end_date: datetime
    average_rate: float
    direction: TrendDirection
    change_percent: float


class FailureAnalysisResponse(BaseModel):
    """Analysis of failures in a time period."""

    total_failures: int
    unique_errors: int
    top_failing_workflows: list[dict[str, Any]]
    top_failing_repositories: list[dict[str, Any]]
    failure_by_day_of_week: dict[str, int]
    most_common_errors: list[dict[str, Any]]
    average_time_to_fix: float | None


class DashboardTrendSummaryResponse(BaseModel):
    """Summary of trends for dashboard."""

    total_runs_today: int
    total_runs_yesterday: int
    runs_change_percent: float
    success_rate_today: float
    success_rate_yesterday: float
    success_rate_direction: TrendDirection
    total_failures_today: int
    total_failures_yesterday: int
    failures_change_percent: float
    avg_duration_seconds: float
    duration_change_percent: float
    most_active_repositories: list[dict[str, Any]]
    most_failing_workflows: list[dict[str, Any]]


class WorkflowTrendResponse(BaseModel):
    """Trend data for a specific workflow."""

    workflow_id: int
    workflow_name: str
    total_runs: int
    success_rate: float
    average_duration_seconds: float
    failure_trend: TrendDirection
    runs_by_day: list[TrendPointResponse]


class RepositoryTrendResponse(BaseModel):
    """Trend data for a specific repository."""

    repository_id: int
    repository_name: str
    total_runs: int
    success_rate: float
    workflows_count: int
    failure_trend: TrendDirection
    top_failing_workflows: list[dict[str, Any]]


def _calculate_direction(values: list[float]) -> TrendDirection:
    """Calculate trend direction from values."""
    if len(values) < 2:
        return TrendDirection.STABLE

    third = max(1, len(values) // 3)
    first_avg = sum(values[:third]) / third
    last_avg = sum(values[-third:]) / third

    threshold = 0.05
    if last_avg > first_avg * (1 + threshold):
        return TrendDirection.UP
    elif last_avg < first_avg * (1 - threshold):
        return TrendDirection.DOWN
    return TrendDirection.STABLE


def _generate_sample_points(
    start: datetime,
    end: datetime,
    period: TrendPeriod,
    base_value: float = 0.85,
    variance: float = 0.1,
) -> list[TrendPointResponse]:
    """Generate sample data points for demonstration."""
    import random  # nosec B311 - used for demo/mock data only

    points = []
    current = start

    if period == TrendPeriod.HOURLY:
        delta = timedelta(hours=1)
    elif period == TrendPeriod.DAILY:
        delta = timedelta(days=1)
    elif period == TrendPeriod.WEEKLY:
        delta = timedelta(weeks=1)
    else:
        delta = timedelta(days=30)

    while current <= end:
        value = base_value + random.uniform(-variance, variance)
        value = max(0, min(1, value))  # Clamp to 0-1 for rates
        points.append(
            TrendPointResponse(
                timestamp=current,
                value=round(value, 4),
                count=random.randint(10, 50),
            )
        )
        current += delta

    return points


@router.get("/success-rate", response_model=SuccessRateTrendResponse)
async def get_success_rate_trend(
    period: TrendPeriod = Query(default=TrendPeriod.DAILY),
    days: int = Query(default=30, ge=1, le=365),
    repository_id: int | None = Query(default=None),
    workflow_id: int | None = Query(default=None),
) -> SuccessRateTrendResponse:
    """Get success rate trend over time."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Generate sample data (would be replaced with actual DB query)
    points = _generate_sample_points(start_date, end_date, period, base_value=0.85)

    values = [p.value for p in points]
    direction = _calculate_direction(values)
    average = sum(values) / len(values) if values else 0

    change_percent = 0.0
    if len(values) >= 2 and values[0] > 0:
        change_percent = ((values[-1] - values[0]) / values[0]) * 100

    return SuccessRateTrendResponse(
        period=period,
        points=points,
        start_date=start_date,
        end_date=end_date,
        average_rate=round(average * 100, 2),
        direction=direction,
        change_percent=round(change_percent, 2),
    )


@router.get("/failures", response_model=FailureAnalysisResponse)
async def get_failure_analysis(
    days: int = Query(default=30, ge=1, le=365),
    repository_id: int | None = Query(default=None),
) -> FailureAnalysisResponse:
    """Get detailed failure analysis."""
    # This would query actual data from DB
    return FailureAnalysisResponse(
        total_failures=42,
        unique_errors=15,
        top_failing_workflows=[
            {"id": 1, "name": "CI Build", "count": 15},
            {"id": 2, "name": "Tests", "count": 12},
            {"id": 3, "name": "Deploy", "count": 8},
        ],
        top_failing_repositories=[
            {"id": 1, "name": "org/repo1", "count": 20},
            {"id": 2, "name": "org/repo2", "count": 12},
        ],
        failure_by_day_of_week={
            "Monday": 8,
            "Tuesday": 6,
            "Wednesday": 10,
            "Thursday": 7,
            "Friday": 11,
            "Saturday": 0,
            "Sunday": 0,
        },
        most_common_errors=[
            {"error": "Test timeout", "count": 10},
            {"error": "Build failed", "count": 8},
            {"error": "Dependency error", "count": 6},
        ],
        average_time_to_fix=3.5,  # hours
    )


@router.get("/summary", response_model=DashboardTrendSummaryResponse)
async def get_trend_summary() -> DashboardTrendSummaryResponse:
    """Get summary of trends for dashboard."""
    import random  # nosec B311 - used for demo/mock data only

    # This would query actual data from DB
    today_runs = random.randint(50, 100)
    yesterday_runs = random.randint(50, 100)
    runs_change = ((today_runs - yesterday_runs) / yesterday_runs * 100) if yesterday_runs else 0

    today_rate = random.uniform(0.80, 0.95)
    yesterday_rate = random.uniform(0.80, 0.95)

    rate_direction = TrendDirection.STABLE
    if today_rate > yesterday_rate * 1.05:
        rate_direction = TrendDirection.UP
    elif today_rate < yesterday_rate * 0.95:
        rate_direction = TrendDirection.DOWN

    today_failures = int(today_runs * (1 - today_rate))
    yesterday_failures = int(yesterday_runs * (1 - yesterday_rate))
    failures_change = (
        ((today_failures - yesterday_failures) / yesterday_failures * 100)
        if yesterday_failures
        else 0
    )

    return DashboardTrendSummaryResponse(
        total_runs_today=today_runs,
        total_runs_yesterday=yesterday_runs,
        runs_change_percent=round(runs_change, 2),
        success_rate_today=round(today_rate * 100, 2),
        success_rate_yesterday=round(yesterday_rate * 100, 2),
        success_rate_direction=rate_direction,
        total_failures_today=today_failures,
        total_failures_yesterday=yesterday_failures,
        failures_change_percent=round(failures_change, 2),
        avg_duration_seconds=random.uniform(120, 300),
        duration_change_percent=random.uniform(-10, 10),
        most_active_repositories=[
            {"id": 1, "name": "org/repo1", "runs": 25},
            {"id": 2, "name": "org/repo2", "runs": 18},
            {"id": 3, "name": "org/repo3", "runs": 12},
        ],
        most_failing_workflows=[
            {"id": 1, "name": "CI Build", "failures": 5},
            {"id": 2, "name": "Deploy", "failures": 3},
        ],
    )


@router.get("/workflow/{workflow_id}", response_model=WorkflowTrendResponse)
async def get_workflow_trend(
    workflow_id: int,
    days: int = Query(default=30, ge=1, le=365),
) -> WorkflowTrendResponse:
    """Get trend data for a specific workflow."""
    import random  # nosec B311 - used for demo/mock data only

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    points = _generate_sample_points(
        start_date, end_date, TrendPeriod.DAILY, base_value=20, variance=10
    )
    # Adjust values for run counts
    for point in points:
        point.value = int(point.value * 3)

    return WorkflowTrendResponse(
        workflow_id=workflow_id,
        workflow_name=f"Workflow-{workflow_id}",
        total_runs=sum(int(p.value) for p in points),
        success_rate=round(random.uniform(0.75, 0.95) * 100, 2),
        average_duration_seconds=random.uniform(60, 300),
        failure_trend=TrendDirection.STABLE,
        runs_by_day=points,
    )


@router.get("/repository/{repository_id}", response_model=RepositoryTrendResponse)
async def get_repository_trend(
    repository_id: int,
    days: int = Query(default=30, ge=1, le=365),
) -> RepositoryTrendResponse:
    """Get trend data for a specific repository."""
    import random  # nosec B311 - used for demo/mock data only

    return RepositoryTrendResponse(
        repository_id=repository_id,
        repository_name=f"org/repo-{repository_id}",
        total_runs=random.randint(100, 500),
        success_rate=round(random.uniform(0.75, 0.95) * 100, 2),
        workflows_count=random.randint(3, 10),
        failure_trend=TrendDirection.STABLE,
        top_failing_workflows=[
            {"id": 1, "name": "CI Build", "failures": random.randint(1, 10)},
            {"id": 2, "name": "Tests", "failures": random.randint(1, 5)},
        ],
    )


@router.get("/duration", response_model=TrendDataResponse)
async def get_duration_trend(
    period: TrendPeriod = Query(default=TrendPeriod.DAILY),
    days: int = Query(default=30, ge=1, le=365),
    workflow_id: int | None = Query(default=None),
) -> TrendDataResponse:
    """Get workflow duration trend over time."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Generate sample duration data (in seconds)
    points = _generate_sample_points(start_date, end_date, period, base_value=180, variance=60)
    # Adjust for duration values
    for point in points:
        point.value = max(30, point.value * 200)

    values = [p.value for p in points]
    direction = _calculate_direction(values)

    change_percent = 0.0
    if len(values) >= 2 and values[0] > 0:
        change_percent = ((values[-1] - values[0]) / values[0]) * 100

    return TrendDataResponse(
        metric_type="avg_duration",
        period=period,
        points=points,
        start_date=start_date,
        end_date=end_date,
        direction=direction,
        average=sum(values) / len(values) if values else 0,
        minimum=min(values) if values else 0,
        maximum=max(values) if values else 0,
        total=sum(values),
        change_percent=round(change_percent, 2),
    )


@router.get("/runs-count", response_model=TrendDataResponse)
async def get_runs_count_trend(
    period: TrendPeriod = Query(default=TrendPeriod.DAILY),
    days: int = Query(default=30, ge=1, le=365),
    repository_id: int | None = Query(default=None),
) -> TrendDataResponse:
    """Get workflow runs count trend over time."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Generate sample run count data
    points = _generate_sample_points(start_date, end_date, period, base_value=50, variance=20)
    # Adjust for count values
    for point in points:
        point.value = max(1, int(point.value * 100))

    values = [p.value for p in points]
    direction = _calculate_direction(values)

    change_percent = 0.0
    if len(values) >= 2 and values[0] > 0:
        change_percent = ((values[-1] - values[0]) / values[0]) * 100

    return TrendDataResponse(
        metric_type="total_runs",
        period=period,
        points=points,
        start_date=start_date,
        end_date=end_date,
        direction=direction,
        average=sum(values) / len(values) if values else 0,
        minimum=min(values) if values else 0,
        maximum=max(values) if values else 0,
        total=sum(values),
        change_percent=round(change_percent, 2),
    )
