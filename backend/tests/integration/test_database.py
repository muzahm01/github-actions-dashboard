"""Integration tests for database operations using testcontainers."""
import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Skip all tests in this module if Docker is not available
pytest.importorskip("testcontainers")
try:
    from testcontainers.postgres import PostgresContainer
except Exception:
    pytest.skip("Docker not available", allow_module_level=True)


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for module-scoped async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Imports below must come after pytest.importorskip to properly skip tests
# ruff: noqa: E402, I001
from app.infrastructure.database.models import (
    Job,
    Log,
    Repository,
    Workflow,
    WorkflowRun,
)
from app.infrastructure.database.models.base import Base
from app.infrastructure.database.repositories.job_repo import JobRepository
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.database.repositories.repository_repo import RepositoryRepository
from app.infrastructure.database.repositories.workflow_run_repo import WorkflowRunRepository


def unique_id() -> int:
    """Generate a unique integer ID for tests."""
    return abs(hash(uuid.uuid4())) % 2147483647


@pytest.fixture(scope="module")
def postgres_container():
    """Start PostgreSQL container with pgvector for integration tests."""
    with PostgresContainer("pgvector/pgvector:pg16") as postgres:
        yield postgres


@pytest.fixture(scope="module")
def database_url(postgres_container) -> str:
    """Get async database URL from container."""
    # Convert psycopg2 URL to asyncpg URL
    url = postgres_container.get_connection_url()
    return url.replace("psycopg2", "asyncpg")


@pytest_asyncio.fixture(scope="module")
async def db_engine(database_url: str):
    """Create async database engine."""
    engine = create_async_engine(database_url, echo=False)

    # Create pgvector extension and tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    """Create async database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.mark.integration
class TestRepositoryRepository:
    """Integration tests for RepositoryRepository."""

    @pytest_asyncio.fixture
    async def repo(self, db_session: AsyncSession) -> RepositoryRepository:
        """Create repository instance."""
        return RepositoryRepository(db_session)

    @pytest_asyncio.fixture
    async def sample_repository(self, db_session: AsyncSession) -> Repository:
        """Create a sample repository in the database."""
        repository = Repository(
            github_id=unique_id(),
            name="test-repo",
            full_name=f"org/test-repo-{unique_id()}",
            owner="org",
            description="Test repository",
            is_active=True,
        )
        db_session.add(repository)
        await db_session.commit()
        await db_session.refresh(repository)
        return repository

    async def test_create_repository(self, repo: RepositoryRepository, db_session: AsyncSession):
        """Should create a new repository."""
        gid = unique_id()
        repository = Repository(
            github_id=gid,
            name="new-repo",
            full_name=f"org/new-repo-{gid}",
            owner="org",
            description="New repository",
            is_active=True,
        )

        created = await repo.create(repository)

        assert created.id is not None
        assert created.github_id == gid
        assert created.name == "new-repo"

    async def test_get_by_id(
        self, repo: RepositoryRepository, sample_repository: Repository
    ):
        """Should get repository by ID."""
        result = await repo.get_by_id(sample_repository.id)

        assert result is not None
        assert result.id == sample_repository.id
        assert result.github_id == sample_repository.github_id

    async def test_get_by_github_id(
        self, repo: RepositoryRepository, sample_repository: Repository
    ):
        """Should get repository by GitHub ID."""
        result = await repo.get_by_github_id(sample_repository.github_id)

        assert result is not None
        assert result.github_id == sample_repository.github_id

    async def test_get_active_repositories(
        self, repo: RepositoryRepository, sample_repository: Repository
    ):
        """Should return only active repositories."""
        results = await repo.get_active()

        assert len(results) >= 1
        assert all(r.is_active for r in results)

    async def test_update_repository(
        self, repo: RepositoryRepository, sample_repository: Repository
    ):
        """Should update repository."""
        sample_repository.description = "Updated description"
        updated = await repo.update(sample_repository)

        assert updated.description == "Updated description"


@pytest.mark.integration
class TestWorkflowRunRepository:
    """Integration tests for WorkflowRunRepository."""

    @pytest_asyncio.fixture
    async def repo(self, db_session: AsyncSession) -> WorkflowRunRepository:
        """Create repository instance."""
        return WorkflowRunRepository(db_session)

    @pytest_asyncio.fixture
    async def sample_workflow(self, db_session: AsyncSession) -> Workflow:
        """Create sample workflow with parent repository."""
        gid = unique_id()
        repository = Repository(
            github_id=gid,
            name="workflow-test-repo",
            full_name=f"org/workflow-test-repo-{gid}",
            owner="org",
            is_active=True,
        )
        db_session.add(repository)
        await db_session.commit()
        await db_session.refresh(repository)

        wid = unique_id()
        workflow = Workflow(
            github_id=wid,
            name="CI",
            path=".github/workflows/ci.yml",
            state="active",
            repo_id=repository.id,
        )
        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)
        return workflow

    @pytest_asyncio.fixture
    async def sample_runs(
        self, db_session: AsyncSession, sample_workflow: Workflow
    ) -> list[WorkflowRun]:
        """Create sample workflow runs."""
        runs = []
        base_id = unique_id()
        for i in range(5):
            run = WorkflowRun(
                github_id=base_id + i,
                run_number=i + 1,
                run_attempt=1,
                status="completed",
                conclusion="success" if i % 2 == 0 else "failure",
                head_branch="main",
                head_sha=f"sha{i}abc123",
                event="push",
                actor="developer",
                html_url=f"https://github.com/org/repo/runs/{base_id+i}",
                workflow_id=sample_workflow.id,
            )
            db_session.add(run)
            runs.append(run)
        await db_session.commit()
        for run in runs:
            await db_session.refresh(run)
        return runs

    async def test_get_by_workflow_id(
        self, repo: WorkflowRunRepository, sample_runs: list[WorkflowRun], sample_workflow: Workflow
    ):
        """Should get runs by workflow ID."""
        results = await repo.get_by_workflow_id(sample_workflow.id)

        assert len(results) == 5
        assert all(r.workflow_id == sample_workflow.id for r in results)

    async def test_get_recent_failures(
        self, repo: WorkflowRunRepository, sample_runs: list[WorkflowRun]
    ):
        """Should get only failed runs."""
        results = await repo.get_recent_failures()

        assert len(results) >= 2
        assert all(r.conclusion == "failure" for r in results)

    async def test_get_by_branch(
        self, repo: WorkflowRunRepository, sample_runs: list[WorkflowRun], sample_workflow: Workflow
    ):
        """Should get runs by branch."""
        results = await repo.get_by_branch(sample_workflow.id, "main")

        assert len(results) >= 1
        assert all(r.head_branch == "main" for r in results)


@pytest.mark.integration
class TestJobRepository:
    """Integration tests for JobRepository."""

    @pytest_asyncio.fixture
    async def repo(self, db_session: AsyncSession) -> JobRepository:
        """Create repository instance."""
        return JobRepository(db_session)

    @pytest_asyncio.fixture
    async def sample_run(self, db_session: AsyncSession) -> WorkflowRun:
        """Create sample workflow run with parent entities."""
        gid = unique_id()
        repository = Repository(
            github_id=gid,
            name="job-test-repo",
            full_name=f"org/job-test-repo-{gid}",
            owner="org",
            is_active=True,
        )
        db_session.add(repository)
        await db_session.commit()

        wid = unique_id()
        workflow = Workflow(
            github_id=wid,
            name="CI",
            path=".github/workflows/ci.yml",
            state="active",
            repo_id=repository.id,
        )
        db_session.add(workflow)
        await db_session.commit()

        rid = unique_id()
        run = WorkflowRun(
            github_id=rid,
            run_number=1,
            run_attempt=1,
            status="completed",
            conclusion="failure",
            head_branch="main",
            head_sha="sha123abc456",
            event="push",
            actor="developer",
            html_url=f"https://github.com/org/repo/runs/{rid}",
            workflow_id=workflow.id,
        )
        db_session.add(run)
        await db_session.commit()
        await db_session.refresh(run)
        return run

    @pytest_asyncio.fixture
    async def sample_jobs(
        self, db_session: AsyncSession, sample_run: WorkflowRun
    ) -> list[Job]:
        """Create sample jobs."""
        jobs = []
        base_id = unique_id()
        for i, (name, conclusion) in enumerate([("build", "success"), ("test", "failure")]):
            job = Job(
                github_id=base_id + i,
                name=name,
                status="completed",
                conclusion=conclusion,
                runner_name="GitHub Actions",
                run_id=sample_run.id,
            )
            db_session.add(job)
            jobs.append(job)
        await db_session.commit()
        for job in jobs:
            await db_session.refresh(job)
        return jobs

    async def test_get_by_run_id(
        self, repo: JobRepository, sample_jobs: list[Job], sample_run: WorkflowRun
    ):
        """Should get jobs by run ID."""
        results = await repo.get_by_run_id(sample_run.id)

        assert len(results) == 2
        assert all(j.run_id == sample_run.id for j in results)

    async def test_get_failed_jobs(
        self, repo: JobRepository, sample_jobs: list[Job], sample_run: WorkflowRun
    ):
        """Should get only failed jobs for a run."""
        results = await repo.get_failed_jobs(sample_run.id)

        assert len(results) >= 1
        assert all(j.conclusion == "failure" for j in results)


@pytest.mark.integration
class TestLogRepository:
    """Integration tests for LogRepository."""

    @pytest_asyncio.fixture
    async def repo(self, db_session: AsyncSession) -> LogRepository:
        """Create repository instance."""
        return LogRepository(db_session)

    @pytest_asyncio.fixture
    async def sample_job(self, db_session: AsyncSession) -> Job:
        """Create sample job with parent entities."""
        gid = unique_id()
        repository = Repository(
            github_id=gid,
            name="log-test-repo",
            full_name=f"org/log-test-repo-{gid}",
            owner="org",
            is_active=True,
        )
        db_session.add(repository)
        await db_session.commit()

        wid = unique_id()
        workflow = Workflow(
            github_id=wid,
            name="CI",
            path=".github/workflows/ci.yml",
            state="active",
            repo_id=repository.id,
        )
        db_session.add(workflow)
        await db_session.commit()

        rid = unique_id()
        run = WorkflowRun(
            github_id=rid,
            run_number=1,
            run_attempt=1,
            status="completed",
            conclusion="failure",
            head_branch="main",
            head_sha="sha789xyz012",
            event="push",
            actor="dev",
            html_url=f"https://github.com/org/repo/runs/{rid}",
            workflow_id=workflow.id,
        )
        db_session.add(run)
        await db_session.commit()

        jid = unique_id()
        job = Job(
            github_id=jid,
            name="test",
            status="completed",
            conclusion="failure",
            runner_name="runner",
            run_id=run.id,
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)
        return job

    async def test_create_and_get_log(
        self, repo: LogRepository, sample_job: Job, db_session: AsyncSession
    ):
        """Should create and retrieve log."""
        log = Log(
            log_content="Test log content with errors",
            log_hash=f"hash-{unique_id()}",
            log_size_bytes=100,
            error_content="Error: something went wrong",
            job_id=sample_job.id,
        )

        created = await repo.create(log)
        assert created.id is not None

        retrieved = await repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.log_content == "Test log content with errors"
        assert retrieved.error_content == "Error: something went wrong"

    async def test_get_by_job_id(
        self, repo: LogRepository, sample_job: Job, db_session: AsyncSession
    ):
        """Should get logs by job ID."""
        log = Log(
            log_content="Job log content",
            log_hash=f"hash-{unique_id()}",
            log_size_bytes=50,
            job_id=sample_job.id,
        )
        db_session.add(log)
        await db_session.commit()

        results = await repo.get_by_job_id(sample_job.id)

        assert len(results) >= 1
        assert all(r.job_id == sample_job.id for r in results)
