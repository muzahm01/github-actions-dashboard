"""Workflow model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.repository import Repository
    from app.infrastructure.database.models.workflow_run import WorkflowRun


class Workflow(Base, TimestampMixin):
    """GitHub workflow definition."""

    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    state: Mapped[str] = mapped_column(String(50), default="active")

    # Relationships
    repository: Mapped[Repository] = relationship(back_populates="workflows")
    workflow_runs: Mapped[list[WorkflowRun]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
