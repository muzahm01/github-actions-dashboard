"""Domain events module."""

from app.domain.events.base import DomainEvent, EventHandler
from app.domain.events.workflow_events import (
    WorkflowRunStarted,
    WorkflowRunCompleted,
    WorkflowRunFailed,
    JobCompleted,
    JobFailed,
)
from app.domain.events.analysis_events import (
    ErrorAnalysisRequested,
    ErrorAnalysisCompleted,
)
from app.domain.events.notification_events import (
    NotificationRequested,
    NotificationSent,
    NotificationFailed,
)

__all__ = [
    "DomainEvent",
    "EventHandler",
    "WorkflowRunStarted",
    "WorkflowRunCompleted",
    "WorkflowRunFailed",
    "JobCompleted",
    "JobFailed",
    "ErrorAnalysisRequested",
    "ErrorAnalysisCompleted",
    "NotificationRequested",
    "NotificationSent",
    "NotificationFailed",
]
