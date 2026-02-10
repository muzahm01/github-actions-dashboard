"""Celery tasks for workflow synchronization."""

import asyncio
import hashlib
import logging
import re
from collections.abc import Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from celery import Task

from app.application.services.test_result_parser import TestResultParserService
from app.config import get_settings
from app.infrastructure.database.models.log import Log
from app.infrastructure.database.models.test_result import (
    TestResult as TestResultModel,
)
from app.infrastructure.database.repositories.job_repo import JobRepository
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.database.repositories.repository_repo import RepositoryRepository
from app.infrastructure.database.repositories.test_result_repo import (
    TestResultRepository,
)
from app.infrastructure.database.repositories.workflow_run_repo import WorkflowRunRepository
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.external.github_client import GitHubClient
from app.infrastructure.websocket.pubsub import (
    publish_test_results_parsed,
    publish_workflow_run_update,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


_T = TypeVar("_T")


def run_async(coro: Coroutine[Any, Any, _T]) -> _T:
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, soft_time_limit=300, time_limit=360, rate_limit="30/m")  # type: ignore[misc]
def sync_repository(self: Task, owner: str, repo: str) -> dict[str, Any]:
    """Sync a single repository's workflows and runs."""
    logger.info(f"Syncing repository: {owner}/{repo}")

    async def _sync() -> dict[str, Any]:
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


def _extract_error_content(log_content: str) -> tuple[str | None, str | None]:
    """
    Extract error content and category from log.

    Returns (error_content, category) tuple.
    """
    if not log_content:
        return None, None

    # Common error patterns
    error_patterns = [
        # Python errors
        (r"(?:Traceback \(most recent call last\):[\s\S]*?(?:Error|Exception):.*)", "python_error"),
        (r"((?:Error|Exception|Failure):.*(?:\n.*){0,10})", "generic_error"),
        # Test failures
        (r"(FAILED.*(?:\n.*){0,5})", "test_failure"),
        (r"(AssertionError:.*(?:\n.*){0,5})", "assertion_error"),
        # Build errors
        (r"(error\[E\d+\]:.*(?:\n.*){0,5})", "rust_error"),
        (r"(error TS\d+:.*(?:\n.*){0,5})", "typescript_error"),
        (r"(SyntaxError:.*(?:\n.*){0,5})", "syntax_error"),
        # Exit codes
        (r"(Process completed with exit code \d+.*)", "exit_code_error"),
    ]

    for pattern, category in error_patterns:
        match = re.search(pattern, log_content, re.IGNORECASE | re.MULTILINE)
        if match:
            error_content = match.group(1)
            # Limit error content to 10000 characters
            return error_content[:10000], category

    # If no specific error found but log contains error indicators
    error_indicators = ["error", "failed", "failure", "exception"]
    if any(ind in log_content.lower() for ind in error_indicators):
        # Extract last 2000 characters as likely error context
        return log_content[-2000:], "unknown_error"

    return None, None


@celery_app.task(bind=True, max_retries=3, soft_time_limit=300, time_limit=360, rate_limit="30/m")  # type: ignore[misc]
def process_workflow_run(self: Task, owner: str, repo: str, run_id: int) -> dict[str, Any]:
    """Process a workflow run - fetch jobs and logs, parse test results, save to database."""
    logger.info(f"Processing workflow run: {owner}/{repo}#{run_id}")

    async def _process() -> dict[str, Any]:
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
                test_results_saved = 0
                log_repo = LogRepository(session)
                job_repo = JobRepository(session)
                test_result_repo = TestResultRepository(session)

                # Initialize test result parser service
                parser_service = TestResultParserService()

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
                                # Find the job in our database
                                db_job = await job_repo.get_by_github_id(job.id)
                                if db_job:
                                    # Extract error content and category
                                    error_content, category = _extract_error_content(log_content)

                                    # Create log entry with error content
                                    new_log = Log(
                                        job_id=db_job.id,
                                        log_content=log_content,
                                        log_size_bytes=len(log_content.encode()),
                                        log_hash=log_hash,
                                        error_content=error_content,
                                        category=category,
                                    )
                                    created_log = await log_repo.create(new_log)
                                    logs_saved += 1
                                    logger.info(
                                        f"Saved log for job {job.id}, "
                                        f"size: {len(log_content)} bytes, "
                                        f"category: {category}"
                                    )

                                    # Parse test results from log
                                    test_result = parser_service.parse(log_content)
                                    if test_result:
                                        # Convert failures to JSON-serializable format
                                        parsed_failures = None
                                        if test_result.failures:
                                            parsed_failures = [
                                                {
                                                    "test_name": f.test_name,
                                                    "error_message": f.error_message,
                                                    "stack_trace": f.stack_trace,
                                                    "file_path": f.file_path,
                                                    "line_number": f.line_number,
                                                }
                                                for f in test_result.failures
                                            ]

                                        # Save test result to database
                                        test_result_model = TestResultModel(
                                            log_id=created_log.id,
                                            framework=test_result.framework,
                                            total_tests=test_result.total,
                                            passed=test_result.passed,
                                            failed=test_result.failed,
                                            skipped=test_result.skipped,
                                            duration_seconds=test_result.duration_seconds,
                                            parsed_failures=parsed_failures,
                                        )
                                        await test_result_repo.create(test_result_model)
                                        test_results_saved += 1
                                        logger.info(
                                            f"Parsed test results for job {job.id}: "
                                            f"framework={test_result.framework}, "
                                            f"total={test_result.total}, "
                                            f"passed={test_result.passed}, "
                                            f"failed={test_result.failed}"
                                        )

                                        # Publish WebSocket event for test results
                                        publish_test_results_parsed(
                                            log_id=created_log.id,
                                            framework=test_result.framework,
                                            total=test_result.total,
                                            passed=test_result.passed,
                                            failed=test_result.failed,
                                            data={
                                                "job_id": db_job.id,
                                                "skipped": test_result.skipped,
                                                "duration_seconds": test_result.duration_seconds,
                                            },
                                        )
                    except Exception as e:
                        logger.warning(f"Failed to fetch/save logs for job {job.id}: {e}")

                await session.commit()

                result = {
                    "run_id": run_id,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "jobs": len(jobs),
                    "failed_jobs": len(failed_jobs),
                    "logs_saved": logs_saved,
                    "test_results_saved": test_results_saved,
                }

                # Publish WebSocket event for workflow run update
                publish_workflow_run_update(
                    run_id=run_id,
                    status=run.status,
                    conclusion=run.conclusion,
                    data={
                        "repository": f"{owner}/{repo}",
                        "jobs_count": len(jobs),
                        "failed_jobs_count": len(failed_jobs),
                        "logs_saved": logs_saved,
                        "test_results_saved": test_results_saved,
                    },
                )

                return result
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


@celery_app.task(soft_time_limit=600, time_limit=660, rate_limit="5/m")  # type: ignore[misc]
def sync_all_workflows() -> dict[str, Any]:
    """Sync all configured repositories (scheduled task)."""
    logger.info("Starting scheduled workflow sync")

    async def _sync_all() -> dict[str, Any]:
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


@celery_app.task(soft_time_limit=300, time_limit=360)  # type: ignore[misc]
def cleanup_old_data() -> dict[str, Any]:
    """Clean up old workflow data based on retention policy."""
    logger.info(f"Cleaning up data older than {settings.data_retention_days} days")

    async def _cleanup() -> dict[str, Any]:
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
