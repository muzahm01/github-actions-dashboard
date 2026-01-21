"""Celery tasks for workflow synchronization."""

import asyncio
import hashlib
import logging
from datetime import UTC, datetime, timedelta

from app.config import get_settings
from app.infrastructure.database.models.log import Log
from app.infrastructure.database.repositories.job_repo import JobRepository
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.database.repositories.repository_repo import RepositoryRepository
from app.infrastructure.database.repositories.workflow_run_repo import WorkflowRunRepository
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.external.github_client import GitHubClient
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def run_async(coro):  # type: ignore[no-untyped-def]
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def sync_repository(self, owner: str, repo: str) -> dict:  # type: ignore[no-untyped-def]
    """Sync a single repository's workflows and runs."""
    logger.info(f"Syncing repository: {owner}/{repo}")

    async def _sync() -> dict:
        client = GitHubClient(settings)
        try:
            # Get repository info
            repo_info = await client.get_repository(owner, repo)

            # Get workflows
            workflows = await client.list_workflows(owner, repo)

            # Get recent runs for each workflow
            total_runs = 0
            for workflow in workflows:
                runs = await client.list_workflow_runs(
                    owner, repo, workflow_id=workflow.id, per_page=10
                )
                total_runs += len(runs)

            return {
                "repository": repo_info.full_name,
                "workflows": len(workflows),
                "runs_synced": total_runs,
            }
        finally:
            await client.close()

    try:
        return run_async(_sync())
    except Exception as e:
        logger.error(f"Failed to sync {owner}/{repo}: {e}")
        raise self.retry(exc=e, countdown=60) from e


@celery_app.task(bind=True, max_retries=3)
def process_workflow_run(self, owner: str, repo: str, run_id: int) -> dict:  # type: ignore[no-untyped-def]
    """Process a workflow run - fetch jobs and logs, save to database."""
    logger.info(f"Processing workflow run: {owner}/{repo}#{run_id}")

    async def _process() -> dict:
        client = GitHubClient(settings)
        session_factory = get_session_factory()

        async with session_factory() as session:
            try:
                # Get run details from GitHub
                run = await client.get_workflow_run(owner, repo, run_id)

                # Get jobs from GitHub
                jobs = await client.list_jobs_for_run(owner, repo, run_id)

                # Download logs for failed jobs and save to database
                failed_jobs = [j for j in jobs if j.conclusion == "failure"]
                logs_saved = 0
                log_repo = LogRepository(session)
                job_repo = JobRepository(session)

                for job in failed_jobs:
                    try:
                        # Download log content
                        log_content = await client.download_job_logs(owner, repo, job.id)
                        if log_content:
                            # Generate hash for deduplication
                            log_hash = hashlib.sha256(log_content.encode()).hexdigest()

                            # Check if log already exists
                            existing_log = await log_repo.get_by_hash(log_hash)
                            if not existing_log:
                                # Find or create the job in our database
                                db_job = await job_repo.get_by_github_id(job.id)
                                if db_job:
                                    # Create log entry
                                    new_log = Log(
                                        job_id=db_job.id,
                                        log_content=log_content,
                                        log_size_bytes=len(log_content.encode()),
                                        log_hash=log_hash,
                                    )
                                    await log_repo.create(new_log)
                                    logs_saved += 1
                                    logger.info(
                                        f"Saved log for job {job.id}, "
                                        f"size: {len(log_content)} bytes"
                                    )
                    except Exception as e:
                        logger.warning(f"Failed to fetch/save logs for job {job.id}: {e}")

                await session.commit()

                return {
                    "run_id": run_id,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "jobs": len(jobs),
                    "failed_jobs": len(failed_jobs),
                    "logs_saved": logs_saved,
                }
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await client.close()

    try:
        return run_async(_process())
    except Exception as e:
        logger.error(f"Failed to process run {run_id}: {e}")
        raise self.retry(exc=e, countdown=60) from e


@celery_app.task
def sync_all_workflows() -> dict:
    """Sync all configured repositories (scheduled task)."""
    logger.info("Starting scheduled workflow sync")

    async def _sync_all() -> dict:
        session_factory = get_session_factory()

        async with session_factory() as session:
            repo_repo = RepositoryRepository(session)

            # Get all active repositories
            active_repos = await repo_repo.get_active()
            repos_synced = 0

            for repo in active_repos:
                try:
                    # Queue sync task for each repository
                    owner, name = repo.full_name.split("/")
                    sync_repository.delay(owner, name)
                    repos_synced += 1
                except Exception as e:
                    logger.error(f"Failed to queue sync for {repo.full_name}: {e}")

            return {
                "status": "completed",
                "repositories_synced": repos_synced,
            }

    return run_async(_sync_all())


@celery_app.task
def cleanup_old_data() -> dict:
    """Clean up old workflow data based on retention policy."""
    logger.info(f"Cleaning up data older than {settings.data_retention_days} days")

    async def _cleanup() -> dict:
        session_factory = get_session_factory()
        cutoff_date = datetime.now(UTC) - timedelta(days=settings.data_retention_days)

        async with session_factory() as session:
            try:
                run_repo = WorkflowRunRepository(session)
                log_repo = LogRepository(session)

                # Get old runs
                old_runs = await run_repo.get_runs_before_date(cutoff_date)
                deleted_runs = 0
                deleted_logs = 0

                for run in old_runs:
                    # Delete associated logs first (cascade should handle this, but being explicit)
                    for job in run.jobs:
                        logs = await log_repo.get_by_job_id(job.id)
                        for log in logs:
                            await log_repo.delete(log)
                            deleted_logs += 1

                    # Delete the run (cascades to jobs)
                    await run_repo.delete(run)
                    deleted_runs += 1

                await session.commit()

                logger.info(f"Cleanup complete: deleted {deleted_runs} runs, {deleted_logs} logs")

                return {
                    "status": "completed",
                    "deleted_runs": deleted_runs,
                    "deleted_logs": deleted_logs,
                    "cutoff_date": cutoff_date.isoformat(),
                }
            except Exception as e:
                await session.rollback()
                logger.error(f"Cleanup failed: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                }

    return run_async(_cleanup())
