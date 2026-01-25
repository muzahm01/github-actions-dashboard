"""Initial migration with all models

Revision ID: 36983138172a
Revises:
Create Date: 2026-01-25 06:49:15.166111

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '36983138172a'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create repositories table
    op.create_table('repositories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('owner', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('webhook_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id')
    )
    op.create_index('ix_repositories_full_name', 'repositories', ['full_name'])
    op.create_index('ix_repositories_is_active', 'repositories', ['is_active'])

    # Create workflows table
    op.create_table('workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.BigInteger(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['repo_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id')
    )
    op.create_index('ix_workflows_repo_id', 'workflows', ['repo_id'])

    # Create workflow_runs table
    op.create_table('workflow_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.BigInteger(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('run_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('conclusion', sa.String(length=50), nullable=True),
        sa.Column('event', sa.String(length=100), nullable=False),
        sa.Column('head_branch', sa.String(length=255), nullable=True),
        sa.Column('head_sha', sa.String(length=40), nullable=False),
        sa.Column('run_started_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id')
    )
    op.create_index('ix_workflow_runs_workflow_id', 'workflow_runs', ['workflow_id'])
    op.create_index('ix_workflow_runs_status', 'workflow_runs', ['status'])
    op.create_index('ix_workflow_runs_conclusion', 'workflow_runs', ['conclusion'])
    op.create_index('ix_workflow_runs_created_at', 'workflow_runs', [sa.text('created_at DESC')])

    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.BigInteger(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('conclusion', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('runner_name', sa.String(length=255), nullable=True),
        sa.Column('runner_labels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['run_id'], ['workflow_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id')
    )
    op.create_index('ix_jobs_run_id', 'jobs', ['run_id'])

    # Create job_steps table
    op.create_table('job_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('conclusion', sa.String(length=50), nullable=True),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_steps_job_id', 'job_steps', ['job_id'])

    # Create logs table
    op.create_table('logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('log_content', sa.Text(), nullable=False),
        sa.Column('log_hash', sa.String(length=64), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('has_test_results', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_errors', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_content', sa.Text(), nullable=True),
        sa.Column('error_lines', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('log_hash')
    )
    op.create_index('ix_logs_job_id', 'logs', ['job_id'])
    op.create_index('ix_logs_has_errors', 'logs', ['has_errors'])
    # Create vector index for similarity search
    op.execute(
        'CREATE INDEX ix_logs_embedding ON logs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )

    # Create test_results table
    op.create_table('test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.Integer(), nullable=False),
        sa.Column('framework', sa.String(length=50), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('passed', sa.Integer(), nullable=False),
        sa.Column('failed', sa.Integer(), nullable=False),
        sa.Column('skipped', sa.Integer(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('parsed_failures', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['log_id'], ['logs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_results_log_id', 'test_results', ['log_id'])
    op.create_index('ix_test_results_framework', 'test_results', ['framework'])

    # Create error_analyses table
    op.create_table('error_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.Integer(), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=False),
        sa.Column('error_summary', sa.Text(), nullable=False),
        sa.Column('suggested_fixes', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('prevention_tips', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('related_documentation', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['log_id'], ['logs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_error_analyses_log_id', 'error_analyses', ['log_id'])
    # Create vector index for similarity search
    op.execute(
        'CREATE INDEX ix_error_analyses_embedding ON error_analyses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)'
    )

    # Create artifacts table
    op.create_table('artifacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.BigInteger(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('expired', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['run_id'], ['workflow_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id')
    )
    op.create_index('ix_artifacts_run_id', 'artifacts', ['run_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('artifacts')
    op.drop_table('error_analyses')
    op.drop_table('test_results')
    op.drop_table('logs')
    op.drop_table('job_steps')
    op.drop_table('jobs')
    op.drop_table('workflow_runs')
    op.drop_table('workflows')
    op.drop_table('repositories')

    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS vector')
