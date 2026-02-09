"""Job model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.job_step import JobStep
    from app.infrastructure.database.models.log import Log
    from app.infrastructure.database.models.workflow_run import WorkflowRun


class Job(Base, TimestampMixin):
    """Job within a workflow run."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"), nullable=False, index=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    conclusion: Mapped[str | None] = mapped_column(String(50), index=True)
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    runner_name: Mapped[str | None] = mapped_column(String(255))
    runner_group: Mapped[str | None] = mapped_column(String(255))
    runner_labels: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    html_url: Mapped[str | None] = mapped_column(Text)

    # Relationships
    run: Mapped[WorkflowRun] = relationship(back_populates="jobs")
    steps: Mapped[list[JobStep]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    logs: Mapped[list[Log]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
