"""Add missing indexes to FK and query columns

Revision ID: a1b2c3d4e5f6
Revises: 36983138172a
Create Date: 2026-02-09 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "36983138172a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # FK indexes
    op.create_index(op.f("ix_artifacts_run_id"), "artifacts", ["run_id"])
    op.create_index(op.f("ix_jobs_run_id"), "jobs", ["run_id"])
    op.create_index(op.f("ix_job_steps_job_id"), "job_steps", ["job_id"])
    op.create_index(op.f("ix_logs_job_id"), "logs", ["job_id"])
    op.create_index(op.f("ix_logs_step_id"), "logs", ["step_id"])
    op.create_index(op.f("ix_test_results_log_id"), "test_results", ["log_id"])
    op.create_index(op.f("ix_workflows_repo_id"), "workflows", ["repo_id"])
    op.create_index(op.f("ix_workflow_runs_workflow_id"), "workflow_runs", ["workflow_id"])

    # Query column indexes
    op.create_index(op.f("ix_jobs_conclusion"), "jobs", ["conclusion"])
    op.create_index(op.f("ix_logs_category"), "logs", ["category"])

    # Timestamp indexes (created_at on all tables via TimestampMixin)
    for table in [
        "repositories",
        "workflows",
        "workflow_runs",
        "jobs",
        "job_steps",
        "logs",
        "test_results",
        "artifacts",
        "error_analyses",
    ]:
        op.create_index(op.f(f"ix_{table}_created_at"), table, ["created_at"])


def downgrade() -> None:
    # Drop timestamp indexes
    for table in [
        "error_analyses",
        "artifacts",
        "test_results",
        "logs",
        "job_steps",
        "jobs",
        "workflow_runs",
        "workflows",
        "repositories",
    ]:
        op.drop_index(op.f(f"ix_{table}_created_at"), table_name=table)

    # Drop query column indexes
    op.drop_index(op.f("ix_logs_category"), table_name="logs")
    op.drop_index(op.f("ix_jobs_conclusion"), table_name="jobs")

    # Drop FK indexes
    op.drop_index(op.f("ix_workflow_runs_workflow_id"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflows_repo_id"), table_name="workflows")
    op.drop_index(op.f("ix_test_results_log_id"), table_name="test_results")
    op.drop_index(op.f("ix_logs_step_id"), table_name="logs")
    op.drop_index(op.f("ix_logs_job_id"), table_name="logs")
    op.drop_index(op.f("ix_job_steps_job_id"), table_name="job_steps")
    op.drop_index(op.f("ix_jobs_run_id"), table_name="jobs")
    op.drop_index(op.f("ix_artifacts_run_id"), table_name="artifacts")
