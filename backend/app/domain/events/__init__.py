"""Domain events module."""

from app.domain.events.analysis_events import (
    ErrorAnalysisCompleted,
    ErrorAnalysisRequested,
)
from app.domain.events.base import DomainEvent, EventHandler
from app.domain.events.notification_events import (
    NotificationFailed,
    NotificationRequested,
    NotificationSent,
)
from app.domain.events.workflow_events import (
    JobCompleted,
    JobFailed,
    WorkflowRunCompleted,
    WorkflowRunFailed,
    WorkflowRunStarted,
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
