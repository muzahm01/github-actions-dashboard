"""GitHub API client for fetching workflow data."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.config import Settings
from app.core.exceptions import GitHubAPIError
from app.core.security import validate_github_owner, validate_github_repo

logger = logging.getLogger(__name__)


@dataclass
class GitHubRepository:
    """GitHub repository data."""

    id: int
    name: str
    full_name: str
    owner: str
    description: str | None
    default_branch: str


@dataclass
class GitHubWorkflow:
    """GitHub workflow data."""

    id: int
    name: str
    path: str
    state: str


@dataclass
class GitHubWorkflowRun:
    """GitHub workflow run data."""

    id: int
    run_number: int
    run_attempt: int
    status: str
    conclusion: str | None
    head_branch: str
    head_sha: str
    event: str
    actor: str
    triggering_actor: str | None
    html_url: str
    created_at: datetime
    updated_at: datetime
    run_started_at: datetime | None


@dataclass
class GitHubJob:
    """GitHub job data."""

    id: int
    name: str
    status: str
    conclusion: str | None
    started_at: datetime | None
    completed_at: datetime | None
    runner_name: str | None
    runner_group: str | None
    html_url: str
    steps: list[dict[str, Any]]


class GitHubClient:
    """Async client for GitHub REST API."""

    def __init__(self, settings: Settings) -> None:
        """Initialize with settings."""
        self._token = settings.github_token
        self._base_url = settings.github_api_base_url
        self._org = settings.github_org
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"token {self._token}",
                    "Accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make API request with error handling."""
        client = await self._get_client()
        try:
            response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Log status code only - response may contain sensitive data
            logger.error(
                f"GitHub API error: {e.response.status_code}",
                extra={"path": path, "method": method},
            )
            raise GitHubAPIError(
                f"GitHub API error: {e.response.status_code}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            # Don't log full exception as it may contain tokens
            logger.error(
                f"GitHub API request failed: {type(e).__name__}",
                extra={"path": path, "method": method},
            )
            raise GitHubAPIError("GitHub API request failed") from e

    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        """Get repository details."""
        # Validate input to prevent path traversal
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        data = await self._request("GET", f"/repos/{owner}/{repo}")
        return GitHubRepository(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            owner=data["owner"]["login"],
            description=data.get("description"),
            default_branch=data["default_branch"],
        )

    async def list_org_repos(self, org: str | None = None) -> list[GitHubRepository]:
        """List repositories in an organization."""
        org = validate_github_owner(org or self._org)
        repos = []
        page = 1

        while True:
            data = await self._request(
                "GET",
                f"/orgs/{org}/repos",
                params={"page": page, "per_page": 100},
            )
            if not data:
                break

            for item in data:
                repos.append(
                    GitHubRepository(
                        id=item["id"],
                        name=item["name"],
                        full_name=item["full_name"],
                        owner=item["owner"]["login"],
                        description=item.get("description"),
                        default_branch=item["default_branch"],
                    )
                )
            page += 1
            if len(data) < 100:
                break

        return repos

    async def list_workflows(self, owner: str, repo: str) -> list[GitHubWorkflow]:
        """List workflows in a repository."""
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        data = await self._request("GET", f"/repos/{owner}/{repo}/actions/workflows")
        return [
            GitHubWorkflow(
                id=w["id"],
                name=w["name"],
                path=w["path"],
                state=w["state"],
            )
            for w in data.get("workflows", [])
        ]

    async def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | None = None,
        branch: str | None = None,
        status: str | None = None,
        per_page: int = 30,
    ) -> list[GitHubWorkflowRun]:
        """List workflow runs."""
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        if workflow_id:
            path = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            path = f"/repos/{owner}/{repo}/actions/runs"

        params: dict[str, Any] = {"per_page": per_page}
        if branch:
            params["branch"] = branch
        if status:
            params["status"] = status

        data = await self._request("GET", path, params=params)
        runs = []

        for r in data.get("workflow_runs", []):
            runs.append(
                GitHubWorkflowRun(
                    id=r["id"],
                    run_number=r["run_number"],
                    run_attempt=r["run_attempt"],
                    status=r["status"],
                    conclusion=r.get("conclusion"),
                    head_branch=r["head_branch"],
                    head_sha=r["head_sha"],
                    event=r["event"],
                    actor=r["actor"]["login"],
                    triggering_actor=r.get("triggering_actor", {}).get("login"),
                    html_url=r["html_url"],
                    created_at=datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00")),
                    run_started_at=(
                        datetime.fromisoformat(r["run_started_at"].replace("Z", "+00:00"))
                        if r.get("run_started_at")
                        else None
                    ),
                )
            )

        return runs

    async def get_workflow_run(self, owner: str, repo: str, run_id: int) -> GitHubWorkflowRun:
        """Get a specific workflow run."""
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        r = await self._request("GET", f"/repos/{owner}/{repo}/actions/runs/{run_id}")
        return GitHubWorkflowRun(
            id=r["id"],
            run_number=r["run_number"],
            run_attempt=r["run_attempt"],
            status=r["status"],
            conclusion=r.get("conclusion"),
            head_branch=r["head_branch"],
            head_sha=r["head_sha"],
            event=r["event"],
            actor=r["actor"]["login"],
            triggering_actor=r.get("triggering_actor", {}).get("login"),
            html_url=r["html_url"],
            created_at=datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00")),
            run_started_at=(
                datetime.fromisoformat(r["run_started_at"].replace("Z", "+00:00"))
                if r.get("run_started_at")
                else None
            ),
        )

    async def list_jobs_for_run(self, owner: str, repo: str, run_id: int) -> list[GitHubJob]:
        """List jobs for a workflow run."""
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        data = await self._request("GET", f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs")
        jobs = []

        for j in data.get("jobs", []):
            jobs.append(
                GitHubJob(
                    id=j["id"],
                    name=j["name"],
                    status=j["status"],
                    conclusion=j.get("conclusion"),
                    started_at=(
                        datetime.fromisoformat(j["started_at"].replace("Z", "+00:00"))
                        if j.get("started_at")
                        else None
                    ),
                    completed_at=(
                        datetime.fromisoformat(j["completed_at"].replace("Z", "+00:00"))
                        if j.get("completed_at")
                        else None
                    ),
                    runner_name=j.get("runner_name"),
                    runner_group=j.get("runner_group_name"),
                    html_url=j["html_url"],
                    steps=j.get("steps", []),
                )
            )

        return jobs

    async def download_job_logs(self, owner: str, repo: str, job_id: int) -> str:
        """Download logs for a job."""
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        client = await self._get_client()
        try:
            response = await client.get(
                f"/repos/{owner}/{repo}/actions/jobs/{job_id}/logs",
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 410:
                # Logs expired
                logger.warning(f"Logs expired for job {job_id}")
                return ""
            raise GitHubAPIError(f"Failed to download logs: {e.response.status_code}") from e

    async def rerun_workflow(self, owner: str, repo: str, run_id: int) -> None:
        """Rerun a workflow."""
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        await self._request("POST", f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun")

    async def cancel_workflow_run(self, owner: str, repo: str, run_id: int) -> None:
        """Cancel a workflow run."""
        owner = validate_github_owner(owner)
        repo = validate_github_repo(repo)
        await self._request("POST", f"/repos/{owner}/{repo}/actions/runs/{run_id}/cancel")
