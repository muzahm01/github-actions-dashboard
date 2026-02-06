# CLAUDE.md - AI Assistant Guide

## Project Overview

GitHub Actions Dashboard is a self-hosted web application that monitors and analyzes GitHub Actions workflows across multiple repositories. It features AI-powered error analysis (Claude LLM), vector similarity search for error patterns, real-time WebSocket updates, and multi-framework test result parsing.

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python / FastAPI | 3.12+ / 0.115+ |
| Frontend | Vue 3 / TypeScript | 3.5+ / 5.9+ |
| Database | PostgreSQL + pgvector | 16 |
| Cache/Broker | Redis | 7+ |
| Task Queue | Celery | 5.6+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Backend Pkg Mgr | UV | latest |
| Frontend Pkg Mgr | npm | (uses package-lock.json) |
| Build Tool | Vite | 7.2+ |
| CSS | Tailwind CSS | 4.1+ |
| State Mgmt | Pinia | 3.0+ |
| HTTP Client | Axios (frontend), httpx (backend) | |
| Containerization | Docker + Docker Compose | |
| Monitoring | Prometheus + Grafana | |

## Project Structure

```
github-actions-dashboard/
├── backend/                        # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/                # REST API endpoints (routers)
│   │   ├── application/           # Business logic services
│   │   ├── domain/                # Entities, value objects, events, protocols
│   │   ├── infrastructure/        # DB models, repos, cache, external clients
│   │   ├── tasks/                 # Celery async tasks
│   │   ├── schemas/               # Pydantic request/response models
│   │   ├── core/                  # Exceptions, logging utilities
│   │   ├── config.py              # Pydantic Settings configuration
│   │   └── main.py                # FastAPI app factory + middleware
│   ├── tests/                     # Test suite (unit/, integration/, e2e/, property/)
│   ├── migrations/                # Alembic database migrations
│   └── pyproject.toml             # Dependencies, ruff, mypy, pytest config
├── frontend/                      # Vue 3 + TypeScript SPA
│   ├── src/
│   │   ├── api/                   # Axios API client
│   │   ├── components/            # Reusable Vue components
│   │   ├── views/                 # Page-level components
│   │   ├── stores/                # Pinia state stores
│   │   ├── router/                # Vue Router config
│   │   ├── types/                 # TypeScript interfaces
│   │   ├── App.vue                # Root component
│   │   └── main.ts                # Entry point
│   ├── package.json               # npm dependencies
│   ├── tsconfig.json              # TypeScript config (references app + node)
│   ├── tsconfig.app.json          # App TS config (strict, @/ alias)
│   └── vite.config.ts             # Vite build config
├── monitoring/                    # Prometheus + Grafana configuration
├── docs/                          # Extended documentation
│   ├── ARCHITECTURE.md
│   ├── PROJECT_SPEC.md
│   ├── IMPLEMENTATION_GUIDE.md
│   └── TESTING_GUIDE.md
├── .github/workflows/             # CI/CD pipelines
├── docker-compose.yml             # Full dev stack (7 services)
├── Makefile                       # Development commands
└── .env.example                   # Environment variable template
```

## Architecture

The backend follows **Clean Architecture** with four layers. Dependencies point inward only.

```
API Layer (app/api/)           ← HTTP endpoints, request validation
  ↓
Application Layer (app/application/) ← Business logic, services, use cases
  ↓
Domain Layer (app/domain/)     ← Entities, value objects, protocols (interfaces)
  ↑
Infrastructure Layer (app/infrastructure/) ← DB, cache, external APIs
```

### Key Design Patterns

- **Dependency injection** via constructor (`__init__` with typed params)
- **Protocol-based interfaces** (use `Protocol`, not `ABC`)
- **Async/await** for all I/O operations
- **Repository pattern** for data access
- **Pydantic models** for API request/response schemas
- **Frozen dataclasses** for value objects
- **Celery tasks** for background processing (webhooks, analysis, notifications)

## Development Commands

### Quick Start

```bash
make setup              # Copy .env.example → .env, install backend deps
make build              # Build Docker images
make up                 # Start all 7 services (API, DB, Redis, Celery, Prometheus, Grafana)
make migrate            # Run Alembic database migrations
```

### Backend Development

```bash
cd backend
uv sync                 # Install all dependencies
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Dev server
uv run pytest           # Run all tests
uv run pytest --cov=app --cov-fail-under=85  # Tests with coverage enforcement
uv run pytest -m unit   # Unit tests only
uv run pytest -m integration  # Integration tests only
uv run pytest -n auto   # Parallel test execution
uv run ruff check app tests   # Lint
uv run ruff check --fix app tests  # Lint with auto-fix
uv run ruff format app tests  # Format
uv run mypy app         # Type checking (strict mode)
uv run bandit -r app    # Security scan
```

### Frontend Development

```bash
cd frontend
npm ci                  # Install dependencies (use ci, not install)
npm run dev             # Vite dev server
npm run build           # Type check (vue-tsc) + production build
npm run preview         # Preview production build
```

### Makefile Shortcuts

```bash
make test               # Run pytest
make test-cov           # pytest + coverage (85% minimum)
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-fast          # Parallel tests (pytest-xdist)
make lint               # ruff check + mypy
make lint-fix           # ruff check --fix
make format             # ruff format + ruff check --fix
make format-check       # ruff format --check
make quality            # format-check + lint + test (full CI check locally)
make migrate            # Run Alembic migrations (in Docker)
make migrate-create     # Create new migration
make db-shell           # psql into PostgreSQL
make db-reset           # WARNING: wipes database
```

## Code Quality Requirements

### Backend (Python)

- **Coverage minimum**: 85% (enforced by `--cov-fail-under=85`)
- **Type checking**: mypy in strict mode — all functions must have complete type hints
- **Linting**: Ruff with rules E, F, I, N, W, UP, B, C4, SIM
- **Formatting**: Ruff formatter, 100-char line length
- **Security**: Bandit scanner
- **Python target**: 3.12

### Frontend (TypeScript)

- **Type checking**: `vue-tsc` (strict mode, `noUnusedLocals`, `noUnusedParameters`)
- **Build**: must pass `vue-tsc -b && vite build` without errors
- **Path alias**: `@/` maps to `src/`

## Testing

### Test Structure

```
backend/tests/
├── unit/           # 75% — Fast, isolated, no external deps
├── integration/    # 20% — Real database/Redis via services
├── e2e/            # 5%  — Full stack
├── property/       # Hypothesis property-based tests
└── conftest.py     # Shared fixtures (test_settings, mock_db_session, client)
```

### Pytest Markers

```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Tests with database/Redis
@pytest.mark.e2e           # Full stack tests
@pytest.mark.slow          # Long-running tests
@pytest.mark.llm           # Tests requiring LLM API
```

### Key Testing Patterns

- `asyncio_mode = "auto"` — all async tests run automatically
- `respx` for mocking httpx requests
- `factory_boy` + `faker` for test data generation
- `freezegun` for time-dependent tests
- `hypothesis` for property-based testing
- `pytest-mock` for general mocking
- `--strict-markers` — undefined markers cause errors

### Coverage Exclusions

Models, session, base repos, external clients, Celery tasks, main.py, logging, WebSocket handler, and several newer service modules are excluded from coverage. See `[tool.coverage.run].omit` in `backend/pyproject.toml` for the full list.

## CI/CD Pipelines

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `ci.yml` | Push to main, PRs | Backend lint + test + coverage, frontend type check + build, Docker build (main only) |
| `backend-ci.yml` | Changes in `backend/` | Lint, mypy, pytest with real Postgres/Redis, Bandit security scan |
| `integration-tests.yml` | Every 4 hours, manual | Full docker-compose stack, migrations, integration tests, health checks |
| `regression-tests.yml` | Every 4 hours | Backend + frontend quality checks, auto-creates GitHub issue on failure |
| `docker-build.yml` | Manual/scheduled | Builds and pushes to GHCR |

CI uses **Python 3.12**, **Node 20**, **pgvector:pg16**, and **redis:7-alpine** as service containers.

## Environment Variables

Copy `.env.example` to `.env` and fill in credentials. Key variables:

```
ENVIRONMENT=development|testing|production
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
REDIS_URL=redis://localhost:6379/0
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=...
GITHUB_ORG=...
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
SECRET_KEY=change-me-in-production
```

## Docker Services

The `docker-compose.yml` defines 7 services on a shared `gha-network`:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| postgres | pgvector/pgvector:pg16 | 5432 | Database with vector extension |
| redis | redis:7-alpine | 6379 | Cache + Celery broker |
| api | ./backend | 8000 | FastAPI application |
| celery-worker | ./backend | — | Background task processing |
| celery-beat | ./backend | — | Scheduled task scheduling |
| prometheus | prom/prometheus | 9090 | Metrics collection |
| grafana | grafana/grafana | 3000 | Metrics visualization |

## Code Conventions

### Python Backend

```python
# Type hints required on all functions (mypy strict)
async def get_workflow(workflow_id: int) -> Workflow: ...

# Frozen dataclasses for value objects
@dataclass(frozen=True)
class TestResult:
    framework: str
    total: int
    passed: int
    failed: int

# Constructor-based dependency injection
class MyService:
    def __init__(self, repo: MyRepository, client: ExternalClient) -> None:
        self._repo = repo
        self._client = client

# FastAPI endpoints with Annotated dependencies
@router.get("/{id}")
async def get_resource(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResourceSchema: ...

# Protocols for interfaces (not ABC)
class Parser(Protocol):
    def parse(self, content: str) -> Result: ...

# Structured JSON logging
logger.info("Processing webhook", extra={"repo": repo_name, "run_id": run_id})
```

### TypeScript Frontend

```typescript
// Vue 3 Composition API with <script setup>
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { MyData } from '@/types'

const data = ref<MyData | null>(null)
const isLoading = ref(false)

async function fetchData(): Promise<void> { ... }
</script>

// Pinia stores with Composition API
export const useMyStore = defineStore('myStore', () => {
  const items = ref<Item[]>([])
  const count = computed(() => items.value.length)
  async function load(): Promise<void> { ... }
  return { items, count, load }
})
```

## Important Rules for AI Assistants

1. **Always use UV** for Python dependency management, never pip
2. **Always use npm** for frontend dependency management (not pnpm or yarn)
3. **Run `make quality`** before considering work complete — it runs format check + lint + tests
4. **Type safety is enforced** — all Python code must pass mypy strict, all TS must pass vue-tsc
5. **Async everywhere** — use `async/await` for all I/O operations in the backend
6. **Respect layer boundaries** — domain must not import from infrastructure; API must not bypass application layer
7. **Test coverage** must stay at or above 85%
8. **Line length** is 100 characters for Python (Ruff)
9. **Use `@pytest.mark.*`** markers on all test functions
10. **Alembic for migrations** — never modify DB schema manually
11. **Secrets** go in `.env` only — never commit `.env` files
