"""GitHub synchronization service for syncing workflow data."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.entities.repository import Repository
from app.domain.entities.workflow import Workflow
from app.domain.entities.workflow_run import WorkflowRun
from app.domain.entities.job import Job
from app.domain.value_objects.time_range import TimeRange

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of synchronization operation."""

    repositories_synced: int = 0
    workflows_synced: int = 0
    runs_synced: int = 0
    jobs_synced: int = 0
    errors: list[str] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []

    @property
    def has_errors(self) -> bool:
        """Check if sync had errors."""
        return len(self.errors) > 0

    def add_error(self, error: str) -> None:
        """Add error to result."""
        self.errors.append(error)


class GitHubClient(Protocol):
    """Protocol for GitHub API client."""

    async def get_repositories(self, org: str) -> list[dict]:
        """Get repositories for organization."""
        ...

    async def get_workflows(self, owner: str, repo: str) -> list[dict]:
        """Get workflows for repository."""
        ...

    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | None = None,
        created: str | None = None,
        per_page: int = 30,
    ) -> list[dict]:
        """Get workflow runs."""
        ...

    async def get_jobs_for_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> list[dict]:
        """Get jobs for a workflow run."""
        ...

    async def get_job_logs(
        self,
        owner: str,
        repo: str,
        job_id: int,
    ) -> str:
        """Get logs for a job."""
        ...


class RepositoryStore(Protocol):
    """Protocol for repository storage."""

    async def get_by_github_id(self, github_id: int) -> Repository | None:
        """Get repository by GitHub ID."""
        ...

    async def save(self, repository: Repository) -> Repository:
        """Save repository."""
        ...


class WorkflowStore(Protocol):
    """Protocol for workflow storage."""

    async def get_by_github_id(self, github_id: int) -> Workflow | None:
        """Get workflow by GitHub ID."""
        ...

    async def save(self, workflow: Workflow) -> Workflow:
        """Save workflow."""
        ...


class WorkflowRunStore(Protocol):
    """Protocol for workflow run storage."""

    async def get_by_github_id(self, github_id: int) -> WorkflowRun | None:
        """Get run by GitHub ID."""
        ...

    async def save(self, run: WorkflowRun) -> WorkflowRun:
        """Save run."""
        ...


class JobStore(Protocol):
    """Protocol for job storage."""

    async def get_by_github_id(self, github_id: int) -> Job | None:
        """Get job by GitHub ID."""
        ...

    async def save(self, job: Job) -> Job:
        """Save job."""
        ...


class GitHubSyncService:
    """Service for synchronizing data from GitHub."""

    def __init__(
        self,
        github_client: GitHubClient,
        repository_store: RepositoryStore,
        workflow_store: WorkflowStore,
        run_store: WorkflowRunStore,
        job_store: JobStore,
    ) -> None:
        """Initialize sync service."""
        self._github = github_client
        self._repo_store = repository_store
        self._workflow_store = workflow_store
        self._run_store = run_store
        self._job_store = job_store

    async def sync_organization(self, org: str) -> SyncResult:
        """Sync all repositories and workflows for an organization."""
        result = SyncResult()

        try:
            repos = await self._github.get_repositories(org)

            for repo_data in repos:
                try:
                    repo = await self._sync_repository(repo_data)
                    result.repositories_synced += 1

                    # Sync workflows for repository
                    owner, name = repo.full_name.split("/")
                    workflows = await self._github.get_workflows(owner, name)

                    for workflow_data in workflows:
                        await self._sync_workflow(repo.id, workflow_data)
                        result.workflows_synced += 1

                except Exception as e:
                    logger.error(f"Error syncing repository {repo_data.get('full_name')}: {e}")
                    result.add_error(f"Failed to sync {repo_data.get('full_name')}: {str(e)}")

        except Exception as e:
            logger.error(f"Error syncing organization {org}: {e}")
            result.add_error(f"Organization sync failed: {str(e)}")

        return result

    async def sync_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | None = None,
        time_range: TimeRange | None = None,
    ) -> SyncResult:
        """Sync workflow runs for a repository."""
        result = SyncResult()

        try:
            # Build created filter if time range provided
            created_filter = None
            if time_range:
                created_filter = f">={time_range.start.isoformat()}"

            runs = await self._github.get_workflow_runs(
                owner=owner,
                repo=repo,
                workflow_id=workflow_id,
                created=created_filter,
            )

            for run_data in runs:
                try:
                    run = await self._sync_run(run_data)
                    result.runs_synced += 1

                    # Sync jobs for completed runs
                    if run.is_completed():
                        jobs = await self._github.get_jobs_for_run(
                            owner=owner,
                            repo=repo,
                            run_id=run.github_id,
                        )

                        for job_data in jobs:
                            await self._sync_job(run.id, job_data)
                            result.jobs_synced += 1

                except Exception as e:
                    logger.error(f"Error syncing run {run_data.get('id')}: {e}")
                    result.add_error(f"Failed to sync run {run_data.get('id')}: {str(e)}")

        except Exception as e:
            logger.error(f"Error syncing workflow runs for {owner}/{repo}: {e}")
            result.add_error(f"Workflow runs sync failed: {str(e)}")

        return result

    async def _sync_repository(self, data: dict) -> Repository:
        """Sync a single repository."""
        github_id = data["id"]

        # Check if exists
        existing = await self._repo_store.get_by_github_id(github_id)
        if existing:
            # Update existing
            existing.name = data["name"]
            existing.full_name = data["full_name"]
            existing.default_branch = data.get("default_branch", "main")
            existing.updated_at = datetime.utcnow()
            return await self._repo_store.save(existing)

        # Create new
        repo = Repository.create(
            github_id=github_id,
            name=data["name"],
            full_name=data["full_name"],
            owner=data["owner"]["login"],
            default_branch=data.get("default_branch", "main"),
        )
        return await self._repo_store.save(repo)

    async def _sync_workflow(self, repository_id: int, data: dict) -> Workflow:
        """Sync a single workflow."""
        github_id = data["id"]

        existing = await self._workflow_store.get_by_github_id(github_id)
        if existing:
            existing.name = data["name"]
            existing.path = data["path"]
            existing.state = data.get("state", "active")
            existing.updated_at = datetime.utcnow()
            return await self._workflow_store.save(existing)

        workflow = Workflow.create(
            github_id=github_id,
            repository_id=repository_id,
            name=data["name"],
            path=data["path"],
            state=data.get("state", "active"),
        )
        return await self._workflow_store.save(workflow)

    async def _sync_run(self, data: dict) -> WorkflowRun:
        """Sync a single workflow run."""
        github_id = data["id"]

        existing = await self._run_store.get_by_github_id(github_id)
        if existing:
            existing.status = data["status"]
            existing.conclusion = data.get("conclusion")
            existing.updated_at = datetime.utcnow()
            return await self._run_store.save(existing)

        # Find workflow ID - need to look up by GitHub workflow ID
        workflow = await self._workflow_store.get_by_github_id(data["workflow_id"])
        workflow_id = workflow.id if workflow else 0

        run_started_at = None
        if data.get("run_started_at"):
            run_started_at = datetime.fromisoformat(
                data["run_started_at"].replace("Z", "+00:00")
            )

        run = WorkflowRun.create(
            github_id=github_id,
            workflow_id=workflow_id,
            run_number=data["run_number"],
            name=data.get("name", ""),
            display_title=data.get("display_title", ""),
            status=data["status"],
            head_branch=data.get("head_branch", ""),
            head_sha=data.get("head_sha", ""),
            event=data.get("event", "push"),
            actor=data.get("actor", {}).get("login", ""),
        )
        run.conclusion = data.get("conclusion")
        run.run_started_at = run_started_at
        run.html_url = data.get("html_url", "")
        run.run_attempt = data.get("run_attempt", 1)

        return await self._run_store.save(run)

    async def _sync_job(self, run_id: int, data: dict) -> Job:
        """Sync a single job."""
        github_id = data["id"]

        existing = await self._job_store.get_by_github_id(github_id)
        if existing:
            existing.status = data["status"]
            existing.conclusion = data.get("conclusion")
            existing.updated_at = datetime.utcnow()
            return await self._job_store.save(existing)

        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"].replace("Z", "+00:00"))

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))

        job = Job.create(
            github_id=github_id,
            run_id=run_id,
            name=data["name"],
            status=data["status"],
        )
        job.conclusion = data.get("conclusion")
        job.started_at = started_at
        job.completed_at = completed_at
        job.runner_name = data.get("runner_name", "")
        job.html_url = data.get("html_url", "")

        return await self._job_store.save(job)
