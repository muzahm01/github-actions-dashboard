"""Celery tasks for workflow synchronization."""
import asyncio
import logging

from app.config import get_settings
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
    """Process a workflow run - fetch jobs and logs."""
    logger.info(f"Processing workflow run: {owner}/{repo}#{run_id}")

    async def _process() -> dict:
        client = GitHubClient(settings)
        try:
            # Get run details
            run = await client.get_workflow_run(owner, repo, run_id)

            # Get jobs
            jobs = await client.list_jobs_for_run(owner, repo, run_id)

            # Download logs for failed jobs
            failed_jobs = [j for j in jobs if j.conclusion == "failure"]
            logs_fetched = 0

            for job in failed_jobs:
                try:
                    logs = await client.download_job_logs(owner, repo, job.id)
                    if logs:
                        logs_fetched += 1
                        # TODO: Save logs to database and trigger analysis
                except Exception as e:
                    logger.warning(f"Failed to fetch logs for job {job.id}: {e}")

            return {
                "run_id": run_id,
                "status": run.status,
                "conclusion": run.conclusion,
                "jobs": len(jobs),
                "failed_jobs": len(failed_jobs),
                "logs_fetched": logs_fetched,
            }
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

    # TODO: Get active repositories from database
    # For now, just log that sync would happen
    return {"status": "scheduled_sync_placeholder"}


@celery_app.task
def cleanup_old_data() -> dict:
    """Clean up old workflow data based on retention policy."""
    logger.info(f"Cleaning up data older than {settings.data_retention_days} days")

    # TODO: Implement actual cleanup
    return {"status": "cleanup_placeholder", "retention_days": settings.data_retention_days}
