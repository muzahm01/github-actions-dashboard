"""JobStep model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.job import Job


class JobStep(Base, TimestampMixin):
    """Step within a job."""

    __tablename__ = "job_steps"
    __table_args__ = (UniqueConstraint("job_id", "number", name="uq_job_step_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    conclusion: Mapped[str | None] = mapped_column(String(50))
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    job: Mapped[Job] = relationship(back_populates="steps")
