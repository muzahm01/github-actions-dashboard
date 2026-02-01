# GitHub Actions Dashboard - Project Specification

## Document Purpose
This specification provides Claude CLI with complete requirements to build a GitHub Actions Dashboard with LLM integration. Follow this document sequentially to implement the full system.

---

## 1. Project Overview

### What We're Building
A self-hosted web application that:
- Monitors GitHub Actions workflows across 10-20 repositories
- Provides real-time visibility via webhooks (95%) and API polling (5% fallback)
- Parses test results from 16+ testing frameworks
- Analyzes errors using Claude LLM
- Enables semantic search for similar errors using vector embeddings
- Monitors its own CI/CD (self-monitoring dashboard)

### Success Criteria
- [x] Real-time workflow monitoring via webhooks
- [x] 30-day data retention with automatic cleanup (maintenance tasks)
- [x] Sub-second API response times
- [x] 85%+ test coverage
- [x] Self-monitoring: dashboard tracks its own GitHub Actions
- [x] Production-ready Docker deployment
- [ ] Frontend Vue 3 application (in progress)

---

## 2. Technology Stack

### Backend (Python 3.12+)
```
Package Manager: UV (NOT pip)
Framework: FastAPI 0.115+
ORM: SQLAlchemy 2.0+ with async support
Database: PostgreSQL 16 + pgvector
Task Queue: Celery 5.4+ with Redis
HTTP Client: httpx (async)
LLM: anthropic SDK for Claude, openai SDK for embeddings
Testing: pytest, pytest-asyncio, hypothesis, factory-boy
Code Quality: ruff, mypy (strict mode)
```

### Frontend (Node.js 22+)
```
Package Manager: pnpm 9+
Framework: Vue 3.5+ with Composition API
Build Tool: Vite 6+
Language: TypeScript 5.7+ (strict mode)
State: Pinia 2.3+
Styling: Tailwind CSS 3.4+
Testing: Vitest, Playwright
```

### Infrastructure
```
Containers: Docker 27+, Docker Compose 2.32+
CI/CD: GitHub Actions
Monitoring: Prometheus, Grafana
```

---

## 3. Architecture Principles

### SOLID Principles (Mandatory)
1. **Single Responsibility**: Each class/module has one reason to change
2. **Open/Closed**: Use protocols and dependency injection for extensibility
3. **Liskov Substitution**: Parsers/clients are interchangeable via protocols
4. **Interface Segregation**: Small, focused Protocol classes
5. **Dependency Inversion**: Depend on abstractions, inject implementations

### Clean Architecture Layers
```
┌─────────────────────────────────────────┐
│  API Layer (FastAPI routes)             │
├─────────────────────────────────────────┤
│  Application Layer (Services, Commands) │
├─────────────────────────────────────────┤
│  Domain Layer (Entities, Value Objects) │
├─────────────────────────────────────────┤
│  Infrastructure (DB, External APIs)     │
└─────────────────────────────────────────┘
```

### Python Best Practices
- Use `@dataclass(frozen=True)` for immutable value objects
- Use `Protocol` classes instead of ABC where possible
- Type hints on ALL functions and variables
- Async/await for all I/O operations
- Context managers for resource management
- f-strings for formatting
- Pathlib for file operations

---

## 4. Project Structure

```
github-actions-dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI entry point
│   │   ├── config.py                    # Pydantic Settings
│   │   ├── dependencies.py              # DI container
│   │   │
│   │   ├── api/v1/                      # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── router.py                # Aggregates all routes
│   │   │   ├── workflows.py
│   │   │   ├── runs.py
│   │   │   ├── jobs.py
│   │   │   ├── logs.py
│   │   │   ├── analysis.py
│   │   │   ├── search.py
│   │   │   ├── webhooks.py
│   │   │   └── health.py
│   │   │
│   │   ├── domain/                      # Domain layer
│   │   │   ├── entities/
│   │   │   ├── value_objects/
│   │   │   ├── events/
│   │   │   └── repositories/            # Interfaces only
│   │   │
│   │   ├── application/                 # Application layer
│   │   │   ├── services/
│   │   │   │   ├── github_sync_service.py
│   │   │   │   ├── webhook_processor.py
│   │   │   │   ├── test_result_parser.py
│   │   │   │   ├── error_analyzer.py
│   │   │   │   ├── embedding_service.py
│   │   │   │   └── search_service.py
│   │   │   ├── commands/
│   │   │   └── queries/
│   │   │
│   │   ├── infrastructure/              # Infrastructure layer
│   │   │   ├── database/
│   │   │   │   ├── session.py
│   │   │   │   ├── models/              # SQLAlchemy models
│   │   │   │   └── repositories/        # Implementations
│   │   │   ├── external/
│   │   │   │   ├── github_client.py
│   │   │   │   ├── claude_client.py
│   │   │   │   └── openai_client.py
│   │   │   └── cache/
│   │   │       └── redis_cache.py
│   │   │
│   │   ├── tasks/                       # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── polling_tasks.py
│   │   │   ├── webhook_tasks.py
│   │   │   ├── analysis_tasks.py
│   │   │   └── maintenance_tasks.py
│   │   │
│   │   ├── core/                        # Core utilities
│   │   │   ├── exceptions.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   │
│   │   └── schemas/                     # Pydantic DTOs
│   │
│   ├── migrations/                      # Alembic
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── factories.py
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── property/
│   │   └── e2e/
│   │
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── views/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── composables/
│   │   ├── services/
│   │   ├── types/
│   │   └── router/
│   ├── tests/
│   ├── package.json
│   └── Dockerfile
│
├── docker/
├── .github/workflows/
├── monitoring/
├── scripts/
├── docs/
├── docker-compose.yml
├── docker-compose.test.yml
├── Makefile
└── README.md
```

---

## 5. Database Schema

### Tables Overview
| Table | Purpose |
|-------|---------|
| repositories | GitHub repositories being monitored |
| workflows | GitHub workflow definitions |
| workflow_runs | Individual workflow run instances |
| jobs | Jobs within a workflow run |
| job_steps | Steps within a job |
| logs | Job logs with vector embeddings |
| test_results | Parsed test results from logs |
| error_analyses | LLM-generated error analysis |
| artifacts | Workflow artifacts |
| sync_status | Webhook/polling tracking |

### Key Relationships
```
repositories 1──N workflows 1──N workflow_runs 1──N jobs 1──N job_steps
                                     │                │
                                     │                └── logs (1:1 per job)
                                     │                     └── test_results
                                     │                     └── error_analyses
                                     └── artifacts
```

### Vector Search
- Use pgvector extension for embeddings
- 1536 dimensions (OpenAI text-embedding-3-small)
- IVFFlat index for similarity search
- Cosine similarity for matching

---

## 6. Core Features

### 6.1 Webhook Processing
- Verify GitHub webhook signatures (HMAC SHA-256)
- Handle `workflow_run` and `workflow_job` events
- Idempotency via delivery_id tracking
- Queue processing via Celery
- Priority: HIGH (process within 30 seconds)

### 6.2 Test Result Parsing
Support these 16+ frameworks:

| Language | Frameworks |
|----------|------------|
| Python | pytest, unittest, nose2 |
| JavaScript | Jest, Mocha, Vitest, Playwright |
| Go | go test |
| Ruby | RSpec, Minitest |
| .NET | xUnit, NUnit, MSTest |
| Java | JUnit, TestNG |
| Rust | cargo test |
| PHP | PHPUnit |

Parser requirements:
- Strip Docker container noise (timestamps, prefixes)
- Remove ANSI color codes
- Extract: total, passed, failed, skipped, duration
- Extract failure details: test name, error message, stack trace

### 6.3 Error Analysis (LLM)
- Use Claude claude-sonnet-4-20250514 for analysis
- Cache by log_hash (avoid duplicate LLM calls)
- Generate embeddings for similarity search
- Output: root_cause, error_summary, suggested_fixes, prevention_tips

### 6.4 Semantic Search
- Generate embeddings via OpenAI text-embedding-3-small
- Store in pgvector column
- Search using cosine similarity
- Return similarity scores with results

### 6.5 Self-Monitoring
- Dashboard monitors its own GitHub Actions
- Regression tests run every 4 hours
- Results reported back to the dashboard
- Dedicated "System Health" view

---

## 7. API Endpoints

### Workflows
```
GET  /api/v1/workflows              # List workflows
GET  /api/v1/workflows/{id}         # Get workflow details
```

### Runs
```
GET  /api/v1/runs                   # List runs (paginated, filtered)
GET  /api/v1/runs/{id}              # Get run details with jobs
```

### Jobs
```
GET  /api/v1/jobs/{id}              # Get job details
GET  /api/v1/jobs/{id}/logs         # Get job logs
```

### Analysis
```
POST /api/v1/analysis/analyze       # Analyze error with LLM
GET  /api/v1/analysis/{id}          # Get analysis result
POST /api/v1/analysis/similar       # Find similar errors
```

### Search
```
POST /api/v1/search/semantic        # Semantic search
POST /api/v1/search/text            # Full-text search
```

### Webhooks
```
POST /webhooks/github               # GitHub webhook receiver
```

### Health
```
GET  /health                        # Basic health check
GET  /health/ready                  # Readiness (dependencies)
GET  /health/live                   # Liveness probe
```

---

## 8. Testing Requirements

### Coverage Targets
| Component | Target |
|-----------|--------|
| Domain Layer | 95%+ |
| Application Services | 90%+ |
| API Endpoints | 85%+ |
| Infrastructure | 80%+ |
| **Overall** | **85%+** |

### Test Types
1. **Unit Tests** (75%): Fast, isolated, mocked dependencies
2. **Integration Tests** (20%): Real database, external APIs mocked
3. **E2E Tests** (5%): Full stack, critical user journeys

### Required Test Files
```
tests/
├── conftest.py                    # Shared fixtures
├── factories.py                   # Factory Boy factories
├── unit/
│   ├── application/services/
│   │   ├── test_test_result_parser.py
│   │   ├── test_webhook_processor.py
│   │   ├── test_error_analyzer.py
│   │   └── test_search_service.py
│   └── api/
├── integration/
│   ├── test_database.py
│   ├── test_webhook_flow.py
│   └── test_celery_tasks.py
├── property/
│   └── test_parser_properties.py  # Hypothesis
└── e2e/
    └── test_full_workflow.py
```

---

## 9. CI/CD Workflows

### Required Workflows
1. **backend-ci.yml**: Lint, type-check, test backend
2. **frontend-ci.yml**: Lint, test, build frontend
3. **docker-build.yml**: Build and test Docker images
4. **integration-tests.yml**: Full stack tests
5. **regression-tests.yml**: Self-monitoring (every 4 hours)
6. **deploy.yml**: Production deployment

### Self-Monitoring Flow
```
regression-tests.yml runs every 4 hours
          │
          ▼
    Run full E2E suite
          │
          ▼
    Report results via webhook
          │
          ▼
    Dashboard displays own health
```

---

## 10. Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# GitHub
GITHUB_TOKEN=ghp_xxx
GITHUB_WEBHOOK_SECRET=xxx
GITHUB_ORG=your-org

# LLM APIs
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Application
ENVIRONMENT=development|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
SECRET_KEY=xxx
```

---

## 11. Implementation Order

Follow this order for implementation:

### Phase 1: Foundation (Week 1-2)
1. Initialize UV project with dependencies
2. Create project structure
3. Implement config.py and main.py
4. Create database models
5. Set up Alembic migrations
6. Implement GitHub client
7. Create basic API endpoints
8. Write initial tests

### Phase 2: Core Features (Week 3-4)
1. Implement webhook processing
2. Create test result parser (all 16 frameworks)
3. Build log viewer
4. Add filtering and pagination
5. Implement real-time updates (WebSocket)

### Phase 3: LLM Integration (Week 5-6)
1. Integrate Claude API
2. Implement error analysis service
3. Add embedding generation
4. Create semantic search
5. Build similar error detection

### Phase 4: Production (Week 7-8)
1. Complete test coverage (85%+)
2. Docker configuration
3. CI/CD workflows
4. Self-monitoring setup
5. Documentation

---

## 12. Quality Gates

Before considering a component complete:

- [ ] All functions have type hints
- [ ] mypy passes with no errors
- [ ] ruff passes with no warnings
- [ ] Test coverage meets target
- [ ] Integration tests pass
- [ ] Documentation updated

---

## Next Steps

After reading this specification:
1. Read IMPLEMENTATION_GUIDE.md for step-by-step instructions
2. Read ARCHITECTURE.md for technical details
3. Read TESTING_GUIDE.md for test requirements
4. Use CLAUDE_CLI_PROMPTS.md for ready-to-use prompts
