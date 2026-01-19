# GitHub Actions Dashboard - Claude CLI Prompts

## Purpose
This document contains ready-to-use prompts for Claude CLI to implement the GitHub Actions Dashboard. Copy and paste these prompts in sequence.

---

## Quick Start

```bash
# Start Claude CLI in your project directory
cd github-actions-dashboard
claude

# Or start with context files
claude --context docs/PROJECT_SPEC.md
```

---

## Phase 1: Project Setup

### Prompt 1.1: Initialize Backend Project

```
Initialize the backend project structure for a GitHub Actions Dashboard.

Requirements:
- Use UV as package manager (NOT pip)
- Python 3.12+
- Follow clean architecture with these layers: domain, application, infrastructure, api

Create the following:

1. backend/pyproject.toml with these dependencies:
   Core: fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, alembic, asyncpg, pgvector, redis, celery, httpx, anthropic, openai, prometheus-client, python-json-logger, sentry-sdk[fastapi]
   Dev: pytest, pytest-asyncio, pytest-cov, pytest-xdist, pytest-mock, factory-boy, faker, respx, hypothesis, testcontainers, freezegun, ruff, mypy, bandit, pre-commit

2. Directory structure:
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── config.py
   │   ├── dependencies.py
   │   ├── api/v1/
   │   ├── domain/{entities,value_objects,events,repositories}/
   │   ├── application/{services,commands,queries}/
   │   ├── infrastructure/{database/{models,repositories},external,cache}/
   │   ├── tasks/
   │   ├── core/
   │   └── schemas/
   ├── migrations/
   ├── tests/{unit,integration,property,e2e,fixtures}/
   └── Dockerfile

3. Configuration in pyproject.toml for:
   - ruff (line-length=100, Python 3.12 target)
   - mypy (strict mode)
   - pytest (markers for unit, integration, e2e, slow, llm)
   - coverage (85% threshold)

Create all __init__.py files and the basic structure. Use touch commands for empty files.
```

### Prompt 1.2: Create Configuration Module

```
Create the configuration module for the backend.

Create backend/app/config.py with:

1. Pydantic Settings class with these settings:
   - environment: Literal["development", "testing", "production"]
   - debug: bool
   - log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
   
   Database settings:
   - postgres_user, postgres_password, postgres_host, postgres_port, postgres_db
   - computed_field for async database_url (postgresql+asyncpg://...)
   - computed_field for sync database_url (for Alembic)
   
   Redis:
   - redis_url: RedisDsn
   
   GitHub:
   - github_token, github_webhook_secret, github_org
   - github_api_base_url = "https://api.github.com"
   
   LLM APIs:
   - anthropic_api_key, openai_api_key
   - claude_model = "claude-sonnet-4-20250514"
   - openai_embedding_model = "text-embedding-3-small"
   - openai_embedding_dimensions = 1536
   
   Application:
   - secret_key, api_v1_prefix = "/api/v1"
   - data_retention_days = 30
   - rate_limit_requests = 100, rate_limit_period = 60

2. Cached get_settings() function using @lru_cache

Use SettingsConfigDict for .env file support.
```

### Prompt 1.3: Create Main Application

```
Create the main FastAPI application entry point.

Create backend/app/main.py with:

1. Lifespan context manager that:
   - Sets up logging on startup
   - Logs startup message with environment
   - Logs shutdown message

2. create_app() function that:
   - Creates FastAPI app with title, description, version
   - Disables docs in production
   - Adds CORS middleware (allow localhost:3000 and 5173)
   - Adds exception handlers for:
     - AppException -> JSONResponse with status_code, detail, code
     - Generic Exception -> 500 with logged traceback
   - Adds health endpoints:
     - GET /health -> {"status": "healthy"}
     - GET /health/ready -> {"status": "ready", "checks": {...}}
     - GET /health/live -> {"status": "alive"}
   - Placeholder for including API router

3. app = create_app() at module level

Also create backend/app/core/exceptions.py with:
- AppException base class (message, code, status_code, details)
- NotFoundError(resource, identifier)
- ValidationError(message, details)
- GitHubAPIError(message, status_code)
- LLMError(message, provider)
- WebhookValidationError(message)

And backend/app/core/logging.py with:
- setup_logging(level) function using python-json-logger
- Suppress noisy loggers (httpx, httpcore, uvicorn.access)
```

---

## Phase 2: Database Layer

### Prompt 2.1: Create Database Models

```
Create SQLAlchemy models for the GitHub Actions Dashboard.

Create backend/app/infrastructure/database/models/base.py with:
- Naming convention for constraints
- Base declarative class with to_dict() method
- TimestampMixin with created_at, updated_at (using func.now())

Create these models in separate files:

1. repository.py - Repository model:
   - id (PK), github_id (BigInteger, unique), name, full_name (indexed), owner
   - description (Text), is_active (indexed), webhook_configured, last_synced_at
   - Relationship to workflows

2. workflow.py - Workflow model:
   - id (PK), repo_id (FK to repositories), github_id (unique), name, path, state
   - Relationships to repository, workflow_runs

3. workflow_run.py - WorkflowRun model:
   - id (PK), workflow_id (FK), github_id (unique), run_number, run_attempt
   - status, conclusion, head_branch, head_sha, event, actor, triggering_actor
   - html_url, run_started_at, duration_seconds, created_at, updated_at
   - Unique constraint on (workflow_id, run_number, run_attempt)
   - Relationships to workflow, jobs, artifacts

4. job.py - Job model:
   - id (PK), run_id (FK), github_id (unique), name, status, conclusion
   - started_at, completed_at, duration_seconds
   - runner_name, runner_group, runner_labels (JSONB), html_url
   - Relationships to run, steps, logs

5. job_step.py - JobStep model:
   - id (PK), job_id (FK), name, status, conclusion, number
   - started_at, completed_at, duration_seconds
   - Unique constraint on (job_id, number)

6. log.py - Log model:
   - id (PK), job_id (FK), step_id (FK nullable)
   - log_content (Text), log_size_bytes, error_content (Text)
   - error_lines (ARRAY of Integer), log_hash (unique)
   - embedding (Vector(1536)), category
   - Relationships to job, step, test_results, error_analyses

7. test_result.py - TestResult model:
   - id (PK), job_id (FK), framework, total_tests, passed, failed, skipped
   - duration_seconds (Float), raw_output, parsed_failures (JSONB)

8. error_analysis.py - ErrorAnalysis model:
   - id (PK), log_id (FK unique), root_cause, error_summary
   - suggested_fixes (ARRAY), prevention_tips (ARRAY)
   - confidence_score, related_documentation (ARRAY)
   - llm_model, llm_tokens_used, embedding (Vector(1536)), analyzed_at

9. artifact.py - Artifact model:
   - id (PK), run_id (FK), github_id (unique), name, size_bytes
   - expired, expires_at, archive_download_url

Create __init__.py that exports all models.
Use proper type hints with Mapped[].
```

### Prompt 2.2: Create Database Session

```
Create database session management.

Create backend/app/infrastructure/database/session.py with:

1. Async engine creation using create_async_engine:
   - Use settings.database_url
   - echo=settings.debug
   - pool_pre_ping=True
   - pool_size=10, max_overflow=20

2. AsyncSessionLocal using async_sessionmaker:
   - class_=AsyncSession
   - expire_on_commit=False
   - autoflush=False

3. Async generator get_db() that:
   - Creates session using context manager
   - Yields session
   - Commits on success
   - Rollbacks on exception
   - Properly closes session

This will be used as FastAPI dependency.
```

### Prompt 2.3: Create Alembic Migration

```
Set up Alembic for database migrations.

1. Create backend/alembic.ini with:
   - script_location = migrations
   - sqlalchemy.url placeholder (will be overridden)

2. Create backend/migrations/env.py with:
   - Import settings for database URL
   - Import Base.metadata from models
   - Configure for async migrations
   - run_migrations_offline() function
   - run_migrations_online() function with async engine

3. Create initial migration in backend/migrations/versions/:
   - Enable pgvector extension: CREATE EXTENSION IF NOT EXISTS vector
   - Create all tables defined in models
   - Create indexes including:
     - Vector similarity indexes using ivfflat
     - Full-text search index on logs.log_content
   - Create timestamp update trigger function
   - Apply triggers to relevant tables

Name the migration: 001_initial_schema.py
```

---

## Phase 3: Application Services

### Prompt 3.1: Create Test Result Parser

```
Create a multi-framework test result parser service.

Create backend/app/application/services/test_result_parser.py with:

1. Value objects (use @dataclass(frozen=True)):
   - FailureDetail: test_name, error_message, stack_trace, file_path, line_number
   - TestResult: framework, total, passed, failed, skipped, duration_seconds, failures
     - Add success_rate property

2. TestResultParser Protocol with:
   - can_parse(log_content: str) -> bool
   - parse(log_content: str) -> TestResult | None

3. BaseParser abstract class with:
   - strip_ansi(text) - remove ANSI color codes
   - strip_docker_noise(text) - remove timestamps, container prefixes
   - preprocess(log_content) - combine above
   - Abstract can_parse() and parse() methods

4. Implement parsers (each with specific regex patterns):
   
   PytestParser:
   - Detect: "collected", "pytest", "===", "passed", "failed"
   - Extract: passed, failed, error, skipped, xfailed, duration
   - Pattern: ===== X passed, Y failed in Z.Zs =====
   
   JestParser:
   - Detect: "Tests:", "passed", "total"
   - Extract: passed, failed, skipped, total, time
   - Pattern: Tests: X failed, Y passed, Z total
   
   GoTestParser:
   - Detect: "--- PASS:", "--- FAIL:", "ok ", "FAIL\t"
   - Count PASS/FAIL/SKIP lines
   - Pattern: ok/FAIL package time
   
   MochaParser:
   - Detect: "passing", "failing", "pending"
   - Pattern: X passing, Y failing
   
   VitestParser:
   - Similar to Jest
   - Pattern: Tests X passed
   
   RSpecParser:
   - Detect: "examples", "failures"
   - Pattern: X examples, Y failures
   
   CargoTestParser:
   - Detect: "test result:", "passed;", "failed;"
   - Pattern: test result: ok/FAILED. X passed; Y failed
   
   PHPUnitParser:
   - Detect: "OK (", "Tests:", "Assertions:"
   - Pattern: OK (X tests, Y assertions)
   
   JUnitParser (Java):
   - Detect: "Tests run:", "Failures:", "Errors:"
   - Pattern: Tests run: X, Failures: Y, Errors: Z
   
   DotNetParser:
   - Detect: "Passed!", "Failed!", "Total tests:"
   - Pattern: Total tests: X, Passed: Y, Failed: Z

5. TestResultParserService class:
   - __init__(parsers=None) - use defaults if none
   - _get_default_parsers() - return all parser instances
   - parse(log_content) - try parsers until one works

Include detailed regex patterns and thorough error handling.
```

### Prompt 3.2: Create Webhook Processor

```
Create webhook processing service with validation and idempotency.

Create backend/app/application/services/webhook_processor.py with:

1. WebhookEvent dataclass (frozen):
   - event_type, action, delivery_id, payload

2. WebhookValidator Protocol:
   - validate(payload: bytes, signature: str) -> bool

3. GitHubWebhookValidator class:
   - __init__(secret: str)
   - validate() using hmac.compare_digest with SHA256
   - Verify signature starts with "sha256="

4. IdempotencyStore Protocol:
   - exists(delivery_id: str) -> bool (async)
   - mark_processed(delivery_id: str) -> None (async)

5. ProcessResult dataclass:
   - status: str ("queued", "duplicate", "error")
   - delivery_id: str
   - message: str | None

6. WebhookProcessor class:
   - __init__(validator, idempotency_store)
   - process(payload, signature, event_type, delivery_id) async:
     - Validate signature (raise WebhookValidationError if invalid)
     - Check idempotency (return "duplicate" if exists)
     - Mark as processed
     - Log with delivery_id
     - Return ProcessResult with "queued"

Use proper logging throughout.
```

### Prompt 3.3: Create GitHub Client

```
Create GitHub API client with rate limiting and retry logic.

Create backend/app/infrastructure/external/github_client.py with:

1. RateLimitInfo dataclass:
   - limit, remaining, reset_at, used

2. GitHubClientProtocol Protocol defining all methods

3. GitHubClient class:
   - __init__(token, base_url, timeout=30)
   - Create httpx.AsyncClient with:
     - Authorization header
     - Accept: application/vnd.github.v3+json
     - User-Agent
     - Timeout
     - Connection pool limits

4. Internal methods:
   - _check_rate_limit(response) - parse headers, log if low
   - _handle_response(response) - raise GitHubAPIError if not OK
   - _request(method, url, **kwargs) - with retry logic:
     - 3 retries with exponential backoff (1s, 2s, 4s)
     - Retry on 5xx errors and rate limits
     - Handle 304 Not Modified

5. API methods (all async):
   - get_rate_limit() -> RateLimitInfo
   - get_repositories(org: str) -> list[dict]
   - get_workflows(owner, repo) -> list[dict]
   - get_workflow_runs(owner, repo, since=None) -> list[dict]
   - get_workflow_run(owner, repo, run_id) -> dict
   - get_jobs_for_run(owner, repo, run_id) -> list[dict]
   - download_job_logs(owner, repo, job_id) -> str
   - get_artifacts(owner, repo, run_id) -> list[dict]

6. Context manager support:
   - __aenter__, __aexit__ for proper cleanup

Use proper pagination for list endpoints.
Log all API calls with timing.
```

### Prompt 3.4: Create LLM Services

```
Create LLM integration services for error analysis and embeddings.

Create backend/app/infrastructure/external/claude_client.py with:

1. LLMClientProtocol Protocol:
   - analyze(prompt: str) -> str (async)

2. ClaudeClient class:
   - __init__(api_key, model, max_tokens)
   - analyze(prompt) async:
     - Call anthropic.messages.create()
     - Handle rate limits and errors
     - Return response text
     - Track token usage in logs

Create backend/app/infrastructure/external/openai_client.py with:

1. EmbeddingClientProtocol Protocol:
   - generate(text: str) -> list[float] (async)
   - generate_batch(texts: list[str]) -> list[list[float]] (async)

2. OpenAIEmbeddingClient class:
   - __init__(api_key, model, dimensions)
   - generate(text) async:
     - Call openai.embeddings.create()
     - Return embedding vector
   - generate_batch(texts) async:
     - Batch up to 100 texts
     - Return list of embeddings

Create backend/app/application/services/error_analyzer.py with:

1. ErrorAnalysis dataclass:
   - root_cause, error_summary, suggested_fixes (list)
   - prevention_tips (list), confidence_score
   - related_documentation (list), model_used, tokens_used

2. ErrorAnalyzerService class:
   - __init__(llm_client, embedding_service, cache, repository)
   - analyze(log: Log) async:
     - Check cache by log_hash
     - Extract error context (truncate if needed)
     - Build analysis prompt
     - Call LLM
     - Parse JSON response
     - Generate embedding
     - Store in database
     - Cache for 7 days
     - Return ErrorAnalysis
   
   - _build_analysis_prompt(error_context) -> str:
     - Request JSON with: root_cause, error_summary, suggested_fixes, prevention_tips, confidence_score
   
   - _extract_error_context(log) -> str:
     - Prioritize error_content if available
     - Truncate to reasonable size (4000 chars)

Create backend/app/application/services/search_service.py with:

1. SearchResult dataclass:
   - log_id, similarity_score, excerpt
   - job_name, workflow_name, repository, occurred_at

2. SearchFilters dataclass:
   - repository_id, date_from, date_to, category

3. SearchService class:
   - __init__(embedding_service, db_session)
   - search_similar_errors(query, limit=10, filters=None) async:
     - Generate query embedding
     - Build SQL with pgvector similarity: 1 - (embedding <=> query_embedding)
     - Apply filters
     - Order by similarity DESC
     - Return SearchResult list
   
   - find_similar_to_log(log_id, limit=5) async:
     - Get log embedding
     - Find similar (excluding self)
```

---

## Phase 4: API Endpoints

### Prompt 4.1: Create API Router Structure

```
Create the API router structure with all endpoints.

Create backend/app/api/v1/router.py that aggregates all routers.

Create these endpoint files in backend/app/api/v1/:

1. health.py:
   - GET / -> {"status": "healthy"}
   - GET /ready -> with dependency checks (db, redis)
   - GET /live -> {"status": "alive"}

2. webhooks.py:
   - POST /github:
     - Headers: X-GitHub-Event, X-Hub-Signature-256, X-GitHub-Delivery
     - Validate signature
     - Check idempotency
     - Queue Celery task based on event type
     - Return 202 Accepted with {"status": "queued", "delivery_id": "..."}

3. workflows.py:
   - GET / -> List workflows with pagination and filters (repo_id)
   - GET /{workflow_id} -> Workflow details with stats

4. runs.py:
   - GET / -> List runs with filters:
     - workflow_id, status, conclusion, branch, event
     - date_from, date_to, page, per_page
   - GET /{run_id} -> Run details with jobs and artifacts

5. jobs.py:
   - GET /{job_id} -> Job details with steps
   - GET /{job_id}/logs -> Job logs with error highlighting

6. analysis.py:
   - POST /analyze -> Analyze error (body: {log_id})
   - GET /{analysis_id} -> Get existing analysis
   - POST /similar -> Find similar errors (body: {log_id, limit})

7. search.py:
   - POST /semantic -> Semantic search (body: {query, limit, filters})
   - POST /text -> Full-text search

Use dependency injection for services.
Add proper request/response models.
Include OpenAPI documentation.
```

### Prompt 4.2: Create Pydantic Schemas

```
Create Pydantic schemas for API request/response models.

Create backend/app/schemas/ with these files:

1. common.py:
   - PaginatedResponse[T] generic model:
     - items: list[T], total: int, page: int, per_page: int, total_pages: int
   - DateRange: start: datetime, end: datetime
   - ErrorResponse: detail: str, code: str

2. repository.py:
   - RepositoryResponse: id, github_id, name, full_name, owner, is_active, last_synced_at
   - RepositoryList: items: list[RepositoryResponse]

3. workflow.py:
   - WorkflowResponse: id, github_id, name, path, state, repository_id
   - WorkflowWithStats: extends WorkflowResponse + success_rate, avg_duration, run_count

4. run.py:
   - WorkflowRunResponse: all run fields
   - WorkflowRunDetail: extends Response + jobs: list[JobSummary], artifacts: list[ArtifactResponse]
   - WorkflowRunFilters: workflow_id, status, conclusion, branch, event, date_from, date_to
   - JobSummary: id, name, status, conclusion, duration_seconds

5. job.py:
   - JobResponse: all job fields
   - JobDetail: extends Response + steps: list[StepResponse]
   - StepResponse: all step fields

6. log.py:
   - LogResponse: id, job_id, log_content, error_content, category
   - LogWithErrors: extends Response + error_lines: list[int]

7. analysis.py:
   - AnalysisRequest: log_id: int
   - AnalysisResponse: id, log_id, root_cause, error_summary, suggested_fixes, prevention_tips, confidence_score, analyzed_at
   - SimilarErrorRequest: log_id: int, limit: int = 5
   - SimilarErrorResponse: log_id, similarity_score, excerpt, job_name, workflow_name, repository, occurred_at

8. search.py:
   - SearchQuery: query: str, limit: int = 10
   - SearchFilters: repository_id, date_from, date_to, category
   - SearchRequest: query: str, limit: int, filters: SearchFilters | None
   - SearchResult: same as SimilarErrorResponse

Use ConfigDict(from_attributes=True) for ORM compatibility.
Add Field() with descriptions for documentation.
```

---

## Phase 5: Celery Tasks

### Prompt 5.1: Create Celery Configuration

```
Create Celery task infrastructure.

Create backend/app/tasks/celery_app.py with:

1. Celery app configuration:
   - broker_url from settings.redis_url
   - result_backend from settings.redis_url
   - task_serializer = "json"
   - result_serializer = "json"
   - accept_content = ["json"]
   - timezone = "UTC"
   - task_track_started = True
   - task_time_limit = 3600
   - task_soft_time_limit = 3300

2. Task routing:
   - webhook tasks -> high priority queue
   - analysis tasks -> default queue
   - polling tasks -> low priority queue
   - maintenance tasks -> low priority queue

3. Celery Beat schedule:
   - sync_all_repositories: every 5 minutes
   - generate_embeddings_batch: every hour
   - cleanup_old_data: daily at 2 AM
   - vacuum_database: weekly on Sunday at 3 AM

Create backend/app/tasks/polling_tasks.py with:
   - sync_all_repositories() task
   - sync_repository(repo_id) task

Create backend/app/tasks/webhook_tasks.py with:
   - process_workflow_run_event(delivery_id, payload) task
   - process_workflow_job_event(delivery_id, payload) task

Create backend/app/tasks/analysis_tasks.py with:
   - analyze_error(log_id) task
   - find_similar_errors(log_id) task

Create backend/app/tasks/embedding_tasks.py with:
   - generate_embedding(log_id) task
   - generate_embeddings_batch() task

Create backend/app/tasks/maintenance_tasks.py with:
   - cleanup_old_data() task
   - vacuum_database() task

Each task should:
- Use proper error handling
- Log start/completion/errors
- Implement retries where appropriate
```

---

## Phase 6: Testing

### Prompt 6.1: Create Test Infrastructure

```
Create test infrastructure with fixtures and factories.

Create backend/tests/conftest.py with:

1. Session-scoped fixtures:
   - postgres_container: PostgresContainer with pgvector
   - redis_container: RedisContainer
   - event_loop: for async tests

2. Test settings fixture:
   - test_settings() using container connection info

3. Database fixtures:
   - db_engine: async engine for tests
   - db_session: session with automatic rollback

4. Client fixture:
   - client: AsyncClient with test app

5. Mock fixtures:
   - mock_github_client: AsyncMock
   - mock_llm_client: AsyncMock
   - mock_embedding_client: AsyncMock

Create backend/tests/factories.py with Factory Boy factories:
   - RepositoryFactory
   - WorkflowFactory
   - WorkflowRunFactory
   - JobFactory
   - JobStepFactory
   - LogFactory
   - TestResultFactory
   - ErrorAnalysisFactory
   - ArtifactFactory

Each factory should:
   - Use SQLAlchemyModelFactory
   - Have realistic default values using Faker
   - Use Sequence for unique fields
   - Use SubFactory for relationships
```

### Prompt 6.2: Create Unit Tests for Parser

```
Create comprehensive unit tests for the test result parser.

Create backend/tests/unit/application/services/test_test_result_parser.py with:

Test classes for each parser:

1. TestPytestParser (15+ tests):
   - test_can_parse_with_collected
   - test_can_parse_with_summary
   - test_cannot_parse_other_frameworks
   - test_parse_all_passed
   - test_parse_with_failures
   - test_parse_with_errors
   - test_parse_with_skipped
   - test_parse_with_xfailed
   - test_parse_extracts_duration
   - test_parse_handles_ansi_codes
   - test_parse_handles_docker_timestamps
   - test_parse_handles_container_prefixes
   - test_parse_extracts_failure_details
   - test_parse_returns_none_for_invalid
   - test_success_rate_calculation

2. TestJestParser (10+ tests):
   - Similar coverage for Jest output patterns

3. TestGoTestParser (10+ tests):
   - Coverage for Go test patterns

4. TestMochaParser (5+ tests)
5. TestVitestParser (5+ tests)
6. TestRSpecParser (5+ tests)
7. TestCargoTestParser (5+ tests)
8. TestPHPUnitParser (5+ tests)
9. TestJUnitParser (5+ tests)
10. TestDotNetParser (5+ tests)

11. TestTestResultParserService (10+ tests):
    - test_selects_correct_parser_for_each_framework
    - test_returns_none_for_unrecognized
    - test_handles_empty_input
    - test_uses_custom_parsers
    - test_preprocess_strips_noise

Create backend/tests/fixtures/log_samples/ with sample logs for each framework.

Target: 95%+ coverage for parser module.
```

### Prompt 6.3: Create Integration Tests

```
Create integration tests for key flows.

Create backend/tests/integration/test_webhook_flow.py:
   - test_webhook_creates_workflow_run
   - test_webhook_updates_existing_run
   - test_webhook_idempotency
   - test_webhook_invalid_signature
   - test_webhook_missing_headers

Create backend/tests/integration/test_database.py:
   - test_create_repository
   - test_create_workflow_with_runs
   - test_cascade_delete
   - test_vector_similarity_search
   - test_full_text_search

Create backend/tests/integration/test_github_api.py (mocked):
   - test_fetch_workflow_runs
   - test_fetch_jobs
   - test_download_logs
   - test_rate_limit_handling
   - test_retry_on_error

Create backend/tests/integration/test_celery_tasks.py:
   - test_sync_repository_task
   - test_process_webhook_task
   - test_analyze_error_task
   - test_generate_embeddings_task

Create backend/tests/property/test_parser_properties.py:
   - test_parser_never_crashes (any input)
   - test_counts_are_consistent
   - test_success_rate_bounded
   - test_handles_any_prefix

Use @pytest.mark.integration and @pytest.mark.slow markers.
```

---

## Phase 7: Docker & CI/CD

### Prompt 7.1: Create Docker Configuration

```
Create Docker configuration for development and production.

Create backend/Dockerfile with multi-stage build:
   - base: Python 3.12-slim + UV
   - development: with dev dependencies, hot reload
   - production: minimal, non-root user, health check

Create frontend/Dockerfile with multi-stage build:
   - builder: Node 22 + pnpm, build static files
   - production: nginx:alpine with built files

Create docker-compose.yml for development:
   - postgres (pgvector/pgvector:pg16)
   - redis (redis:7-alpine)
   - backend (development target, volume mount)
   - celery-worker
   - celery-beat
   - frontend (with hot reload)

Create docker-compose.test.yml for testing:
   - Isolated containers
   - Test database

Create docker-compose.prod.yml for production:
   - Production targets
   - Resource limits
   - Health checks
   - Restart policies

Create docker/nginx/nginx.conf:
   - Reverse proxy to backend
   - Serve frontend static files
   - WebSocket support
   - Gzip compression
   - Security headers
```

### Prompt 7.2: Create GitHub Actions Workflows

```
Create GitHub Actions CI/CD workflows.

Create .github/workflows/backend-ci.yml:
   - Trigger: push/PR to backend/**
   - Jobs:
     - lint: ruff check, ruff format, mypy
     - test: unit + integration with coverage
     - property-tests: Hypothesis tests
     - security: Bandit scan
   - Services: postgres, redis
   - Upload coverage to Codecov
   - Fail if coverage < 85%

Create .github/workflows/frontend-ci.yml:
   - Trigger: push/PR to frontend/**
   - Jobs:
     - lint: eslint, prettier, type-check
     - test: Vitest unit tests
     - e2e: Playwright tests
   - Upload coverage

Create .github/workflows/docker-build.yml:
   - Build and test Docker images
   - Run tests inside containers
   - Cache Docker layers

Create .github/workflows/integration-tests.yml:
   - Full stack integration tests
   - Use docker-compose.test.yml
   - Run on schedule (daily) and PR

Create .github/workflows/regression-tests.yml (SELF-MONITORING):
   - Run every 4 hours
   - Full E2E regression suite
   - Report results back to dashboard via webhook
   - This makes the dashboard monitor itself!

Create .github/workflows/deploy.yml:
   - Trigger: tag push (v*)
   - Build and push images to registry
   - Deploy to server via SSH
```

---

## Utility Prompts

### Run Tests

```
Run all backend tests with coverage and show the results.

Commands to run:
1. uv run pytest tests/unit -v --cov=app --cov-report=term-missing
2. Show coverage summary
3. List any failing tests
4. Suggest fixes for any failures
```

### Fix Linting Issues

```
Run ruff and mypy on the backend code and fix all issues.

1. Run: uv run ruff check . --fix
2. Run: uv run ruff format .
3. Run: uv run mypy app/ --ignore-missing-imports
4. Fix any remaining type errors
5. Show summary of changes made
```

### Add New Parser

```
Add a new test result parser for [FRAMEWORK_NAME].

1. Analyze the typical output format of [FRAMEWORK_NAME] tests
2. Create detection patterns (what makes this framework unique)
3. Create extraction patterns (how to get passed/failed/skipped/duration)
4. Implement [Framework]Parser class in test_result_parser.py
5. Add to default parsers list
6. Create test file: tests/unit/application/services/test_[framework]_parser.py
7. Create sample log file: tests/fixtures/log_samples/[framework]_*.txt
8. Run tests to verify
```

### Database Migration

```
Create a new database migration for the following change:
[DESCRIBE CHANGE]

1. Create migration file using Alembic
2. Write upgrade() function
3. Write downgrade() function
4. Test migration: uv run alembic upgrade head
5. Test rollback: uv run alembic downgrade -1
6. Re-apply: uv run alembic upgrade head
```

### Add API Endpoint

```
Add a new API endpoint: [METHOD] [PATH]

Purpose: [DESCRIPTION]

1. Create/update schema in app/schemas/
2. Create/update endpoint in app/api/v1/
3. Add to router
4. Create unit test in tests/unit/api/
5. Create integration test if needed
6. Update OpenAPI documentation
7. Run tests
```

---

## Debugging Prompts

### Debug Test Failure

```
This test is failing:

[PASTE TEST OUTPUT]

1. Analyze the error message
2. Check the test code
3. Check the implementation
4. Identify the root cause
5. Fix the issue
6. Verify with re-run
```

### Debug Docker Issue

```
Docker container [NAME] is failing with:

[PASTE ERROR]

1. Check container logs: docker logs [NAME]
2. Check configuration
3. Verify environment variables
4. Check network connectivity
5. Propose fix
```

### Performance Investigation

```
The [COMPONENT] is slow. Investigate and optimize.

1. Add timing logs to identify bottleneck
2. Check database queries for N+1 problems
3. Check for missing indexes
4. Identify caching opportunities
5. Implement optimizations
6. Measure improvement
```

---

## Summary

Use these prompts in sequence to build the complete GitHub Actions Dashboard:

1. **Phase 1** (1.1-1.3): Project setup and configuration
2. **Phase 2** (2.1-2.3): Database models and migrations
3. **Phase 3** (3.1-3.4): Application services (parser, webhook, clients)
4. **Phase 4** (4.1-4.2): API endpoints and schemas
5. **Phase 5** (5.1): Celery tasks
6. **Phase 6** (6.1-6.3): Testing infrastructure
7. **Phase 7** (7.1-7.2): Docker and CI/CD

Each prompt is self-contained and builds upon the previous work.
