"""Log model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.error_analysis import ErrorAnalysis
    from app.infrastructure.database.models.job import Job
    from app.infrastructure.database.models.job_step import JobStep
    from app.infrastructure.database.models.test_result import TestResult


class Log(Base, TimestampMixin):
    """Job logs with vector embeddings."""

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    step_id: Mapped[int | None] = mapped_column(ForeignKey("job_steps.id"))
    log_content: Mapped[str | None] = mapped_column(Text)
    log_size_bytes: Mapped[int | None] = mapped_column(Integer)
    error_content: Mapped[str | None] = mapped_column(Text)
    error_lines: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    log_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    category: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    job: Mapped[Job] = relationship(back_populates="logs")
    step: Mapped[JobStep | None] = relationship()
    test_results: Mapped[list[TestResult]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
    )
    error_analyses: Mapped[list[ErrorAnalysis]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
    )
