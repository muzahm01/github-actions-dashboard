# GitHub Actions Dashboard

A self-hosted web application that monitors and analyzes GitHub Actions workflows across multiple repositories with AI-powered error analysis.

## Quick Reference

| Component | Technology | Commands |
|-----------|-----------|----------|
| Backend | Python 3.12+ / FastAPI | `cd backend && uv run uvicorn app.main:app --reload` |
| Frontend | Vue 3 / TypeScript | `cd frontend && pnpm dev` |
| Package Manager (Backend) | UV | `uv sync`, `uv add <pkg>` |
| Package Manager (Frontend) | pnpm | `pnpm install`, `pnpm add <pkg>` |
| Database | PostgreSQL 16 + pgvector | `make db-shell` |
| Cache/Queue | Redis 7+ | via Docker |
| Task Queue | Celery | `uv run celery -A app.tasks.celery_app worker` |

## Project Structure

```
github-actions-dashboard/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # REST API endpoints
│   │   ├── application/       # Business logic (services, commands, queries)
│   │   ├── domain/            # Entities, value objects, events
│   │   ├── infrastructure/    # Database, external APIs, cache
│   │   ├── tasks/             # Celery async tasks
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── core/              # Exceptions, logging utilities
│   │   ├── config.py          # Pydantic Settings configuration
│   │   └── main.py            # FastAPI app factory
│   ├── tests/                 # pytest test suite
│   ├── migrations/            # Alembic database migrations
│   └── pyproject.toml         # UV dependencies & tool config
├── frontend/                  # Vue 3 + TypeScript frontend
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page components
│   │   ├── stores/            # Pinia state stores
│   │   ├── api/               # API client
│   │   └── types/             # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── monitoring/                # Prometheus & Grafana config
├── docs/                      # Documentation
├── .github/workflows/         # GitHub Actions CI/CD
├── docker-compose.yml         # Development stack
└── Makefile                   # Common commands
```

## Architecture

The backend follows **Clean Architecture** with four layers:

1. **API Layer** (`app/api/`) - FastAPI endpoints, request handling
2. **Application Layer** (`app/application/`) - Business logic, services
3. **Domain Layer** (`app/domain/`) - Entities, value objects, business rules
4. **Infrastructure Layer** (`app/infrastructure/`) - Database, external APIs, cache

Key design patterns:
- Dependency injection via constructor
- Protocol-based interfaces (not ABC)
- Async/await for all I/O operations
- Repository pattern for data access

## Development Commands

```bash
# Project setup
make setup              # Copy .env, install deps
make build              # Build Docker images
make up                 # Start all services
make down               # Stop services

# Backend development
cd backend
uv sync                 # Install dependencies
uv run uvicorn app.main:app --reload  # Start dev server
uv run pytest           # Run tests
uv run pytest --cov=app # Tests with coverage
uv run ruff check --fix # Lint and fix
uv run ruff format      # Format code
uv run mypy app         # Type checking

# Frontend development
cd frontend
pnpm install            # Install dependencies
pnpm dev                # Start dev server
pnpm build              # Production build
pnpm test               # Run tests
pnpm lint               # Lint code

# Database
make migrate            # Run migrations
make migrate-create     # Create new migration
make db-shell           # PostgreSQL shell

# Testing
make test               # All tests
make test-cov           # With coverage
make test-unit          # Unit only
make test-integration   # Integration only
make lint               # All linting
make format             # Format all code
make quality            # All checks (format + lint + test)
```

## Code Conventions

### Python (Backend)

```python
# All functions must have type hints
async def get_workflow(workflow_id: int) -> Workflow:
    ...

# Use dataclasses for value objects
@dataclass(frozen=True)
class TestResult:
    framework: str
    total: int
    passed: int
    failed: int

# Service classes with dependency injection
class MyService:
    def __init__(self, repo: MyRepository, client: ExternalClient) -> None:
        self._repo = repo
        self._client = client

    async def do_work(self, data: InputModel) -> OutputModel:
        ...

# API endpoints with proper typing
@router.get("/{id}")
async def get_resource(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResourceSchema:
    ...
```

### TypeScript (Frontend)

```typescript
// Vue 3 Composition API
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { MyData } from '@/types'

const data = ref<MyData | null>(null)
const computed_value = computed(() => data.value?.something)

async function fetchData(): Promise<void> {
  // Implementation
}
</script>
```

## Testing Requirements

- **Minimum coverage**: 85%
- **Test pyramid**: Unit (75%) > Integration (20%) > E2E (5%)
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`

```bash
# Run specific test categories
uv run pytest -m unit              # Unit tests only
uv run pytest -m integration       # Integration tests
uv run pytest -k "test_webhook"    # By pattern
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app factory, middleware |
| `backend/app/config.py` | Pydantic Settings configuration |
| `backend/app/application/services/test_result_parser.py` | Multi-framework test parsing |
| `backend/app/application/services/error_analyzer.py` | LLM-powered error analysis |
| `backend/app/application/services/webhook_processor.py` | Webhook handling |
| `backend/pyproject.toml` | Python dependencies & tool config |
| `docker-compose.yml` | Development infrastructure |
| `Makefile` | Common development commands |

## Environment Variables

Key variables (see `.env.example`):
```
ENVIRONMENT=development|testing|production
DEBUG=true|false
POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
REDIS_URL
GITHUB_TOKEN
GITHUB_WEBHOOK_SECRET
ANTHROPIC_API_KEY
OPENAI_API_KEY
```

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- `ci.yml` - Main CI (lint, test, coverage, Docker build)
- `backend-ci.yml` - Backend-specific checks
- `integration-tests.yml` - Full integration suite
- `docker-build.yml` - Docker image building

## Important Notes

1. **Always use UV** for Python dependency management, not pip
2. **Run tests** before committing: `make quality`
3. **Type safety** is enforced - all code must pass mypy strict mode
4. **Async everywhere** - use `async/await` for all I/O operations
5. **Layered architecture** - respect layer boundaries, inject dependencies
6. **Test coverage** must stay above 85%
