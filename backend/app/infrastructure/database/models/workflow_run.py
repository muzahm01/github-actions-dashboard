"""WorkflowRun model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.artifact import Artifact
    from app.infrastructure.database.models.job import Job
    from app.infrastructure.database.models.workflow import Workflow


class WorkflowRun(Base, TimestampMixin):
    """Individual workflow run instance."""

    __tablename__ = "workflow_runs"
    __table_args__ = (
        UniqueConstraint(
            "workflow_id", "run_number", "run_attempt", name="uq_workflow_run_attempt"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False, index=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    run_attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    conclusion: Mapped[str | None] = mapped_column(String(50), index=True)
    head_branch: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    event: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    triggering_actor: Mapped[str | None] = mapped_column(String(255))
    html_url: Mapped[str | None] = mapped_column(String(500))
    run_started_at: Mapped[datetime | None] = mapped_column()
    duration_seconds: Mapped[int | None] = mapped_column()

    # Relationships
    workflow: Mapped[Workflow] = relationship(back_populates="workflow_runs")
    jobs: Mapped[list[Job]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
    artifacts: Mapped[list[Artifact]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
