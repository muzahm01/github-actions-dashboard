# GitHub Actions Dashboard - Testing Guide

## Purpose
This guide provides comprehensive testing requirements for Claude CLI to ensure 85%+ test coverage with high-quality tests.

---

## 1. Testing Philosophy

### Test Pyramid
```
              ┌─────────────────┐
              │     E2E         │  5% (10 tests)
              │  Full Stack     │  Critical user journeys only
              └────────┬────────┘
           ┌───────────┴───────────┐
           │    Integration        │  20% (40 tests)
           │  Service + Database   │  Real dependencies
           └───────────┬───────────┘
    ┌──────────────────┴──────────────────┐
    │           Unit Tests                │  75% (150+ tests)
    │    Fast, isolated, mocked deps      │
    └─────────────────────────────────────┘
```

### Core Principles
1. **Test behavior, not implementation** - Test what the code does, not how
2. **One assertion per concept** - Multiple asserts OK if testing one thing
3. **Descriptive names** - `test_parse_returns_none_when_log_is_empty`
4. **Arrange-Act-Assert** - Clear test structure
5. **Fast by default** - Unit tests < 100ms each

---

## 2. Coverage Requirements

### By Component
| Component | Target | Rationale |
|-----------|--------|-----------|
| `domain/entities` | 95%+ | Core business logic |
| `domain/value_objects` | 95%+ | Immutable, testable |
| `application/services` | 90%+ | Main use cases |
| `application/commands` | 90%+ | Business operations |
| `api/v1` | 85%+ | Request/response handling |
| `infrastructure/database` | 80%+ | CRUD operations |
| `infrastructure/external` | 80%+ | External API clients |
| `tasks` | 80%+ | Async task logic |
| **Overall** | **85%+** | Project minimum |

### Coverage Commands
```bash
# Run with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# Fail if under threshold
uv run pytest --cov=app --cov-fail-under=85

# Coverage by component
uv run pytest --cov=app/application/services --cov-fail-under=90
```

---

## 3. Test Categories

### 3.1 Unit Tests

**Location:** `tests/unit/`

**Characteristics:**
- No database, network, or file I/O
- All dependencies mocked
- Fast (<100ms per test)
- Isolated (no shared state)

**Required Test Files:**

```
tests/unit/
├── domain/
│   ├── entities/
│   │   └── test_workflow_run.py
│   └── value_objects/
│       ├── test_run_status.py
│       └── test_error_category.py
│
├── application/
│   └── services/
│       ├── test_test_result_parser.py      # CRITICAL
│       ├── test_webhook_processor.py       # CRITICAL
│       ├── test_error_analyzer.py          # CRITICAL
│       ├── test_embedding_service.py
│       ├── test_search_service.py
│       └── test_github_sync_service.py
│
├── api/
│   ├── test_workflows.py
│   ├── test_runs.py
│   ├── test_jobs.py
│   ├── test_webhooks.py
│   ├── test_analysis.py
│   └── test_search.py
│
└── core/
    ├── test_exceptions.py
    └── test_security.py
```

**Example: Unit Test for Test Result Parser**

```python
"""Unit tests for test result parser service."""
import pytest
from unittest.mock import Mock

from app.application.services.test_result_parser import (
    PytestParser,
    JestParser,
    GoTestParser,
    RSpecParser,
    MochaParser,
    VitestParser,
    CargoTestParser,
    TestResultParserService,
    TestResult,
    FailureDetail,
)


class TestPytestParser:
    """Test suite for pytest log parser."""
    
    @pytest.fixture
    def parser(self) -> PytestParser:
        """Create parser instance."""
        return PytestParser()
    
    # Detection tests
    def test_can_parse_with_collected_keyword(self, parser):
        assert parser.can_parse("collected 5 items") is True
    
    def test_can_parse_with_summary_line(self, parser):
        assert parser.can_parse("===== 5 passed in 1.0s =====") is True
    
    def test_cannot_parse_jest_output(self, parser):
        assert parser.can_parse("Tests: 5 passed, 5 total") is False
    
    def test_cannot_parse_empty_log(self, parser):
        assert parser.can_parse("") is False
    
    # Parsing tests - success scenarios
    def test_parse_all_passed(self, parser):
        log = """
        ============================= test session starts ==============================
        collected 10 items
        
        tests/test_example.py ..........                                        [100%]
        
        ============================== 10 passed in 1.23s ==============================
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.framework == "pytest"
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0
        assert result.skipped == 0
        assert result.duration_seconds == pytest.approx(1.23)
    
    def test_parse_with_failures(self, parser):
        log = """
        collected 10 items
        ===== 2 failed, 6 passed, 2 skipped in 3.45s =====
        """
        result = parser.parse(log)
        
        assert result.total == 10
        assert result.passed == 6
        assert result.failed == 2
        assert result.skipped == 2
        assert result.duration_seconds == pytest.approx(3.45)
    
    def test_parse_with_errors(self, parser):
        log = "===== 1 error, 9 passed in 0.5s ====="
        result = parser.parse(log)
        
        assert result.failed == 1  # errors count as failures
        assert result.passed == 9
    
    def test_parse_with_xfailed(self, parser):
        log = "===== 5 passed, 2 xfailed in 1.0s ====="
        result = parser.parse(log)
        
        assert result.passed == 5
        assert result.skipped == 2  # xfailed counts as skipped
    
    # Edge cases
    def test_parse_strips_ansi_codes(self, parser):
        log = "\x1b[32m===== 5 passed in 0.5s =====\x1b[0m"
        result = parser.parse(log)
        
        assert result is not None
        assert result.passed == 5
    
    def test_parse_strips_docker_timestamps(self, parser):
        log = """
        2024-01-15T10:00:00.000Z collected 3 items
        2024-01-15T10:00:01.000Z ===== 3 passed in 0.5s =====
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.passed == 3
    
    def test_parse_strips_container_prefixes(self, parser):
        log = """
        [test-container] collected 2 items
        [test-container] ===== 2 passed in 0.1s =====
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.passed == 2
    
    def test_parse_returns_none_for_invalid_log(self, parser):
        log = "This is not pytest output"
        result = parser.parse(log)
        
        assert result is None
    
    # Failure detail extraction
    def test_extracts_failure_details(self, parser):
        log = """
        collected 2 items
        
        _________________________________ test_example _________________________________
        
        def test_example():
        >       assert 1 == 2
        E       AssertionError: assert 1 == 2
        
        tests/test_example.py:5: AssertionError
        ===== 1 failed, 1 passed in 0.1s =====
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.failed == 1
        assert len(result.failures) >= 1
        assert "test_example" in result.failures[0].test_name
        assert "AssertionError" in result.failures[0].error_message


class TestJestParser:
    """Test suite for Jest log parser."""
    
    @pytest.fixture
    def parser(self) -> JestParser:
        return JestParser()
    
    def test_can_parse_jest_output(self, parser):
        assert parser.can_parse("Tests: 5 passed, 5 total") is True
    
    def test_parse_all_passed(self, parser):
        log = """
        PASS src/test.spec.js
        Tests:        5 passed, 5 total
        Time:         1.234 s
        """
        result = parser.parse(log)
        
        assert result.framework == "jest"
        assert result.passed == 5
        assert result.total == 5
        assert result.duration_seconds == pytest.approx(1.234)
    
    def test_parse_with_failures(self, parser):
        log = "Tests:        2 failed, 3 skipped, 5 passed, 10 total"
        result = parser.parse(log)
        
        assert result.failed == 2
        assert result.skipped == 3
        assert result.passed == 5
        assert result.total == 10


class TestGoTestParser:
    """Test suite for Go test log parser."""
    
    @pytest.fixture
    def parser(self) -> GoTestParser:
        return GoTestParser()
    
    def test_can_parse_go_test_output(self, parser):
        assert parser.can_parse("--- PASS: TestExample (0.00s)") is True
        assert parser.can_parse("ok  \tgithub.com/user/repo\t0.123s") is True
    
    def test_parse_all_passed(self, parser):
        log = """
        === RUN   TestExample1
        --- PASS: TestExample1 (0.00s)
        === RUN   TestExample2
        --- PASS: TestExample2 (0.01s)
        PASS
        ok  	github.com/user/repo	0.123s
        """
        result = parser.parse(log)
        
        assert result.framework == "go-test"
        assert result.passed == 2
        assert result.failed == 0
        assert result.duration_seconds == pytest.approx(0.123)
    
    def test_parse_with_failures(self, parser):
        log = """
        --- PASS: TestA (0.00s)
        --- FAIL: TestB (0.01s)
        --- SKIP: TestC (0.00s)
        FAIL	github.com/user/repo	0.5s
        """
        result = parser.parse(log)
        
        assert result.passed == 1
        assert result.failed == 1
        assert result.skipped == 1


class TestTestResultParserService:
    """Test suite for parser orchestration service."""
    
    @pytest.fixture
    def service(self) -> TestResultParserService:
        return TestResultParserService()
    
    def test_selects_correct_parser_for_pytest(self, service):
        log = "collected 1 items\n===== 1 passed in 0.1s ====="
        result = service.parse(log)
        
        assert result is not None
        assert result.framework == "pytest"
    
    def test_selects_correct_parser_for_jest(self, service):
        log = "Tests: 1 passed, 1 total"
        result = service.parse(log)
        
        assert result is not None
        assert result.framework == "jest"
    
    def test_selects_correct_parser_for_go(self, service):
        log = "--- PASS: Test (0.00s)\nok  \tpkg\t0.1s"
        result = service.parse(log)
        
        assert result is not None
        assert result.framework == "go-test"
    
    def test_returns_none_for_unrecognized_output(self, service):
        log = "Build successful\nDeploying..."
        result = service.parse(log)
        
        assert result is None
    
    def test_handles_empty_log(self, service):
        result = service.parse("")
        assert result is None
    
    def test_handles_none_input(self, service):
        # Should not crash
        try:
            service.parse(None)  # type: ignore
        except (TypeError, AttributeError):
            pass  # Expected
    
    def test_custom_parsers(self):
        """Should use custom parsers when provided."""
        mock_parser = Mock()
        mock_parser.can_parse.return_value = True
        mock_parser.parse.return_value = TestResult(
            framework="custom",
            total=1,
            passed=1,
            failed=0,
            skipped=0,
        )
        
        service = TestResultParserService(parsers=[mock_parser])
        result = service.parse("any log")
        
        assert result is not None
        assert result.framework == "custom"
```

### 3.2 Integration Tests

**Location:** `tests/integration/`

**Characteristics:**
- Use real database (testcontainers)
- External APIs mocked (respx)
- Test service interactions
- Slower (seconds per test)

**Required Test Files:**

```
tests/integration/
├── test_database.py           # CRUD operations
├── test_github_api.py         # GitHub client with mocks
├── test_webhook_flow.py       # Full webhook processing
├── test_celery_tasks.py       # Task execution
├── test_search.py             # Vector search with pgvector
└── test_llm_integration.py    # LLM client with mocks
```

**Example: Integration Test for Webhook Flow**

```python
"""Integration tests for webhook processing flow."""
import hashlib
import hmac
import json

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.models import WorkflowRun


@pytest.mark.integration
class TestWebhookFlow:
    """Integration tests for complete webhook processing."""
    
    @pytest_asyncio.fixture
    async def webhook_secret(self) -> str:
        return "test-webhook-secret"
    
    def _generate_signature(self, payload: bytes, secret: str) -> str:
        """Generate GitHub webhook signature."""
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"
    
    async def test_webhook_creates_workflow_run(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        webhook_secret: str,
    ):
        """Webhook should create workflow run in database."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "run_number": 42,
                "status": "completed",
                "conclusion": "success",
                "head_branch": "main",
                "head_sha": "abc123",
                "event": "push",
                "actor": {"login": "testuser"},
            },
            "repository": {
                "id": 100,
                "name": "test-repo",
                "full_name": "org/test-repo",
                "owner": {"login": "org"},
            },
            "workflow": {
                "id": 200,
                "name": "CI",
                "path": ".github/workflows/ci.yml",
            },
        }
        
        payload_bytes = json.dumps(payload).encode()
        signature = self._generate_signature(payload_bytes, webhook_secret)
        
        response = await client.post(
            "/webhooks/github",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "workflow_run",
                "X-Hub-Signature-256": signature,
                "X-GitHub-Delivery": "test-delivery-001",
            },
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
    
    async def test_webhook_idempotency(
        self,
        client: AsyncClient,
        webhook_secret: str,
    ):
        """Duplicate webhook should be detected."""
        payload = json.dumps({"action": "completed"}).encode()
        signature = self._generate_signature(payload, webhook_secret)
        delivery_id = "test-delivery-duplicate"
        
        headers = {
            "Content-Type": "application/json",
            "X-GitHub-Event": "workflow_run",
            "X-Hub-Signature-256": signature,
            "X-GitHub-Delivery": delivery_id,
        }
        
        # First request
        response1 = await client.post(
            "/webhooks/github",
            content=payload,
            headers=headers,
        )
        
        # Second request with same delivery ID
        response2 = await client.post(
            "/webhooks/github",
            content=payload,
            headers=headers,
        )
        
        assert response1.status_code == 202
        assert response2.status_code == 200
        assert response2.json()["status"] == "duplicate"
    
    async def test_webhook_invalid_signature(
        self,
        client: AsyncClient,
    ):
        """Invalid signature should be rejected."""
        payload = json.dumps({"action": "completed"}).encode()
        
        response = await client.post(
            "/webhooks/github",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "workflow_run",
                "X-Hub-Signature-256": "sha256=invalid",
                "X-GitHub-Delivery": "test-delivery-invalid",
            },
        )
        
        assert response.status_code == 401
```

### 3.3 Property-Based Tests

**Location:** `tests/property/`

**Characteristics:**
- Use Hypothesis for random input generation
- Test invariants and properties
- Find edge cases automatically

**Required Test Files:**

```
tests/property/
├── test_parser_properties.py
├── test_value_objects.py
└── test_serialization.py
```

**Example: Property Tests for Parser**

```python
"""Property-based tests for test result parser."""
import pytest
from hypothesis import given, strategies as st, assume, settings

from app.application.services.test_result_parser import (
    TestResultParserService,
    TestResult,
    PytestParser,
)


class TestParserProperties:
    """Property-based tests for parser behavior."""
    
    @pytest.fixture
    def service(self) -> TestResultParserService:
        return TestResultParserService()
    
    @given(log_content=st.text(max_size=10000))
    @settings(max_examples=200)
    def test_parser_never_crashes(self, service: TestResultParserService, log_content: str):
        """Parser should handle any input without crashing."""
        # Should not raise any exception
        result = service.parse(log_content)
        
        # Result should be None or valid TestResult
        assert result is None or isinstance(result, TestResult)
    
    @given(
        passed=st.integers(min_value=0, max_value=10000),
        failed=st.integers(min_value=0, max_value=10000),
        skipped=st.integers(min_value=0, max_value=10000),
        duration=st.floats(min_value=0, max_value=3600, allow_nan=False),
    )
    def test_test_result_counts_are_consistent(
        self, passed: int, failed: int, skipped: int, duration: float
    ):
        """TestResult counts should always sum to total."""
        result = TestResult(
            framework="test",
            total=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )
        
        assert result.total == result.passed + result.failed + result.skipped
        assert result.total >= 0
        assert result.passed >= 0
        assert result.failed >= 0
        assert result.skipped >= 0
    
    @given(
        total=st.integers(min_value=1, max_value=10000),
        passed=st.integers(min_value=0),
    )
    def test_success_rate_bounded(self, total: int, passed: int):
        """Success rate should always be between 0 and 100."""
        assume(passed <= total)
        
        result = TestResult(
            framework="test",
            total=total,
            passed=passed,
            failed=total - passed,
            skipped=0,
        )
        
        assert 0 <= result.success_rate <= 100
    
    @given(
        prefix=st.sampled_from([
            "",
            "2024-01-15T10:00:00.000Z ",
            "[container] ",
            "\x1b[32m",
        ]),
        passed=st.integers(min_value=0, max_value=100),
    )
    def test_pytest_parser_handles_prefixes(self, prefix: str, passed: int):
        """Pytest parser should handle various log prefixes."""
        parser = PytestParser()
        
        log = f"{prefix}collected {passed} items\n{prefix}===== {passed} passed in 1.0s ====="
        
        if parser.can_parse(log):
            result = parser.parse(log)
            assert result is None or result.passed == passed


class TestValueObjectProperties:
    """Property-based tests for value objects."""
    
    @given(
        test_name=st.text(min_size=1, max_size=200),
        error_message=st.text(min_size=1, max_size=1000),
    )
    def test_failure_detail_is_immutable(self, test_name: str, error_message: str):
        """FailureDetail should be immutable."""
        from app.application.services.test_result_parser import FailureDetail
        
        detail = FailureDetail(
            test_name=test_name,
            error_message=error_message,
        )
        
        # Should not be able to modify
        with pytest.raises(AttributeError):
            detail.test_name = "modified"  # type: ignore
```

### 3.4 End-to-End Tests

**Location:** `tests/e2e/`

**Characteristics:**
- Full stack testing
- Real user journeys
- Slowest tests
- Run less frequently

**Required Test Files:**

```
tests/e2e/
├── test_full_workflow.py
├── test_error_analysis.py
└── test_search_flow.py
```

**Example: E2E Test**

```python
"""End-to-end tests for complete user workflows."""
import pytest
import asyncio


@pytest.mark.e2e
class TestFullWorkflow:
    """E2E tests for complete user journeys."""
    
    async def test_webhook_to_analysis_flow(
        self,
        client,
        db_session,
        mock_github_api,
        mock_llm_api,
    ):
        """
        Complete flow:
        1. Receive webhook for failed run
        2. Fetch job logs from GitHub
        3. Parse test results
        4. Analyze error with LLM
        5. Generate embeddings
        6. Query via API
        """
        # 1. Send webhook
        webhook_response = await client.post(
            "/webhooks/github",
            json=self._create_failed_run_payload(),
            headers=self._webhook_headers(),
        )
        assert webhook_response.status_code == 202
        
        # 2. Wait for async processing
        await asyncio.sleep(2)
        
        # 3. Query the run
        run_response = await client.get("/api/v1/runs/12345")
        assert run_response.status_code == 200
        run_data = run_response.json()
        
        assert run_data["conclusion"] == "failure"
        assert "jobs" in run_data
        
        # 4. Request analysis
        analysis_response = await client.post(
            "/api/v1/analysis/analyze",
            json={"log_id": run_data["jobs"][0]["log_id"]},
        )
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        
        assert "root_cause" in analysis
        assert "suggested_fixes" in analysis
        assert len(analysis["suggested_fixes"]) > 0
        
        # 5. Search for similar errors
        search_response = await client.post(
            "/api/v1/search/semantic",
            json={"query": analysis["root_cause"], "limit": 5},
        )
        assert search_response.status_code == 200
```

---

## 4. Test Fixtures

### 4.1 Shared Fixtures (conftest.py)

```python
"""Shared test fixtures."""
import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from unittest.mock import Mock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from httpx import AsyncClient, ASGITransport

from app.config import Settings
from app.infrastructure.database.models.base import Base
from app.main import create_app


# Session-scoped containers
@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL with pgvector for tests."""
    with PostgresContainer(
        image="pgvector/pgvector:pg16",
        username="test",
        password="test",
        dbname="test_db",
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    """Redis for tests."""
    with RedisContainer() as redis:
        yield redis


# Settings fixture
@pytest.fixture
def test_settings(postgres_container, redis_container) -> Settings:
    """Test configuration."""
    return Settings(
        environment="testing",
        postgres_user="test",
        postgres_password="test",
        postgres_host=postgres_container.get_container_host_ip(),
        postgres_port=int(postgres_container.get_exposed_port(5432)),
        postgres_db="test_db",
        redis_url=f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}/0",
        github_token="test-token",
        github_webhook_secret="test-secret",
        anthropic_api_key="test-key",
        openai_api_key="test-key",
    )


# Database session
@pytest_asyncio.fixture
async def db_session(test_settings) -> AsyncGenerator[AsyncSession, None]:
    """Test database session with automatic rollback."""
    engine = create_async_engine(test_settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


# HTTP client
@pytest_asyncio.fixture
async def client(test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client."""
    app = create_app()
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# Mock fixtures
@pytest.fixture
def mock_github_client():
    """Mocked GitHub client."""
    client = AsyncMock()
    client.get_workflow_runs.return_value = []
    client.get_jobs_for_run.return_value = []
    client.download_job_logs.return_value = ""
    return client


@pytest.fixture
def mock_llm_client():
    """Mocked LLM client."""
    client = AsyncMock()
    client.analyze.return_value = {
        "root_cause": "Test failure",
        "error_summary": "Tests failed",
        "suggested_fixes": ["Fix the code"],
        "prevention_tips": ["Add more tests"],
        "confidence_score": 0.9,
    }
    return client
```

### 4.2 Test Factories (factories.py)

```python
"""Test factories using Factory Boy."""
import factory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime, timezone

from app.infrastructure.database.models import (
    Repository,
    Workflow,
    WorkflowRun,
    Job,
    Log,
)


class RepositoryFactory(SQLAlchemyModelFactory):
    """Factory for Repository model."""
    
    class Meta:
        model = Repository
        sqlalchemy_session = None  # Set in fixture
        sqlalchemy_session_persistence = "commit"
    
    github_id = factory.Sequence(lambda n: 100000 + n)
    name = factory.Faker("word")
    full_name = factory.LazyAttribute(lambda o: f"org/{o.name}")
    owner = "org"
    is_active = True
    webhook_configured = True


class WorkflowFactory(SQLAlchemyModelFactory):
    """Factory for Workflow model."""
    
    class Meta:
        model = Workflow
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
    
    repository = factory.SubFactory(RepositoryFactory)
    github_id = factory.Sequence(lambda n: 200000 + n)
    name = factory.Faker("sentence", nb_words=3)
    path = factory.LazyAttribute(
        lambda o: f".github/workflows/{o.name.lower().replace(' ', '-')}.yml"
    )
    state = "active"


class WorkflowRunFactory(SQLAlchemyModelFactory):
    """Factory for WorkflowRun model."""
    
    class Meta:
        model = WorkflowRun
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
    
    workflow = factory.SubFactory(WorkflowFactory)
    github_id = factory.Sequence(lambda n: 300000 + n)
    run_number = factory.Sequence(lambda n: n + 1)
    run_attempt = 1
    status = "completed"
    conclusion = factory.Faker(
        "random_element",
        elements=["success", "failure", "cancelled"],
    )
    head_branch = "main"
    head_sha = factory.Faker("sha1")
    event = "push"
    actor = factory.Faker("user_name")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class JobFactory(SQLAlchemyModelFactory):
    """Factory for Job model."""
    
    class Meta:
        model = Job
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
    
    run = factory.SubFactory(WorkflowRunFactory)
    github_id = factory.Sequence(lambda n: 400000 + n)
    name = factory.Faker("word")
    status = "completed"
    conclusion = "success"


class LogFactory(SQLAlchemyModelFactory):
    """Factory for Log model."""
    
    class Meta:
        model = Log
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
    
    job = factory.SubFactory(JobFactory)
    log_content = factory.Faker("text", max_nb_chars=1000)
    log_hash = factory.Faker("sha256")
```

---

## 5. Test Data (Fixtures)

### 5.1 Log Samples

Create `tests/fixtures/log_samples/`:

**pytest_success.txt:**
```
============================= test session starts ==============================
platform linux -- Python 3.12.0, pytest-8.0.0, pluggy-1.4.0
rootdir: /app
collected 25 items

tests/test_api.py ..........                                              [ 40%]
tests/test_services.py ...............                                    [100%]

============================== 25 passed in 2.34s ==============================
```

**pytest_failure.txt:**
```
============================= test session starts ==============================
platform linux -- Python 3.12.0, pytest-8.0.0, pluggy-1.4.0
rootdir: /app
collected 10 items

tests/test_example.py .....F....                                          [100%]

=================================== FAILURES ===================================
_________________________________ test_divide __________________________________

    def test_divide():
>       assert divide(10, 0) == 0
E       ZeroDivisionError: division by zero

tests/test_example.py:15: ZeroDivisionError
=========================== short test summary info ============================
FAILED tests/test_example.py::test_divide - ZeroDivisionError: division by zero
========================= 1 failed, 9 passed in 0.52s =========================
```

**jest_success.txt:**
```
PASS  src/__tests__/api.test.js
PASS  src/__tests__/utils.test.js

Test Suites: 2 passed, 2 total
Tests:       15 passed, 15 total
Snapshots:   0 total
Time:        3.456 s
```

**go_test_failure.txt:**
```
=== RUN   TestAdd
--- PASS: TestAdd (0.00s)
=== RUN   TestDivide
    math_test.go:20: expected 5, got 0
--- FAIL: TestDivide (0.01s)
=== RUN   TestMultiply
--- PASS: TestMultiply (0.00s)
FAIL
exit status 1
FAIL	github.com/user/repo/math	0.234s
```

### 5.2 GitHub API Responses

Create `tests/fixtures/github_responses/`:

**workflow_run.json:**
```json
{
  "id": 12345,
  "name": "CI",
  "run_number": 42,
  "status": "completed",
  "conclusion": "failure",
  "head_branch": "main",
  "head_sha": "abc123def456",
  "event": "push",
  "actor": {
    "login": "developer",
    "avatar_url": "https://github.com/images/developer.png"
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z",
  "html_url": "https://github.com/org/repo/actions/runs/12345"
}
```

---

## 6. Running Tests

### Commands

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test category
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e

# Run specific test file
uv run pytest tests/unit/application/services/test_test_result_parser.py

# Run with verbose output
uv run pytest -v

# Run in parallel
uv run pytest -n auto

# Run with specific markers
uv run pytest -m "not slow"
uv run pytest -m "unit and not llm"
```

### pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (with database)
    e2e: End-to-end tests (full stack)
    slow: Slow tests (skip in quick runs)
    llm: Tests requiring LLM API

addopts =
    --strict-markers
    -ra
    --tb=short

filterwarnings =
    ignore::DeprecationWarning
```

---

## 7. CI Integration

### GitHub Actions Test Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python
        run: uv python install 3.12
      
      - name: Install dependencies
        working-directory: backend
        run: uv sync --frozen --all-extras
      
      - name: Run tests with coverage
        working-directory: backend
        run: |
          uv run pytest \
            --cov=app \
            --cov-report=xml \
            --cov-fail-under=85 \
            -n auto
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
          fail_ci_if_error: true
```

---

## Summary Checklist

Before considering testing complete:

- [ ] 85%+ overall coverage
- [ ] All parsers have 10+ test cases each
- [ ] Webhook flow has integration tests
- [ ] Property-based tests for parsers
- [ ] E2E test for critical path
- [ ] All tests pass in CI
- [ ] Test fixtures cover all frameworks
- [ ] Mocks properly isolate external dependencies
