"""Domain entities module."""

from app.domain.entities.repository import Repository
from app.domain.entities.workflow import Workflow
from app.domain.entities.workflow_run import WorkflowRun
from app.domain.entities.job import Job
from app.domain.entities.log import Log
from app.domain.entities.error_analysis import ErrorAnalysis
from app.domain.entities.test_result import TestResult
from app.domain.entities.notification import Notification

__all__ = [
    "Repository",
    "Workflow",
    "WorkflowRun",
    "Job",
    "Log",
    "ErrorAnalysis",
    "TestResult",
    "Notification",
]
