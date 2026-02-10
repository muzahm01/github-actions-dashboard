# Contributing to GitHub Actions Dashboard

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- [UV](https://docs.astral.sh/uv/) (Python package manager)

### Quick Start

```bash
make setup        # Copy .env.example → .env, install backend deps
make build        # Build Docker images
make up           # Start all services
make migrate      # Run database migrations
```

### Backend Development

```bash
cd backend
uv sync                          # Install dependencies
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm ci            # Install dependencies (always use ci, not install)
npm run dev       # Start Vite dev server
```

## Code Quality

Run the full quality check before submitting changes:

```bash
make quality      # Runs format-check + lint + tests
```

### Backend Standards

- **Formatting**: `uv run ruff format app tests` (100-char line length)
- **Linting**: `uv run ruff check app tests`
- **Type checking**: `uv run mypy app` (strict mode — all functions need type hints)
- **Security**: `uv run bandit -r app`
- **Tests**: `uv run pytest --cov=app --cov-fail-under=85`

### Frontend Standards

- **Type checking + build**: `npm run build` (runs `vue-tsc -b && vite build`)

## Testing

### Running Tests

```bash
make test             # All tests
make test-unit        # Unit tests only
make test-integration # Integration tests (requires Docker services)
make test-cov         # Tests with 85% coverage enforcement
make test-fast        # Parallel execution with pytest-xdist
```

### Writing Tests

- Place unit tests in `backend/tests/unit/`, integration tests in `backend/tests/integration/`
- Use `@pytest.mark.unit` or `@pytest.mark.integration` markers on every test
- All async tests run automatically (`asyncio_mode = "auto"`)
- Use `factory_boy` + `faker` for test data, `respx` for HTTP mocks, `pytest-mock` for general mocking

## Architecture

The backend follows **Clean Architecture** with four layers:

```
API (app/api/)  →  Application (app/application/)  →  Domain (app/domain/)  ←  Infrastructure (app/infrastructure/)
```

**Key rules:**
- Domain must not import from Infrastructure
- API must not bypass the Application layer
- Use `Protocol` (not `ABC`) for domain interfaces
- Use `async/await` for all I/O operations
- Use constructor-based dependency injection

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, focused commits
3. Ensure `make quality` passes locally
4. Submit a PR with a description of what changed and why
5. Address review feedback

## Dependency Management

- **Backend**: Use `uv` — never `pip install` directly
- **Frontend**: Use `npm ci` — never `yarn` or `pnpm`
- Pin exact versions in `pyproject.toml` and `package.json`

## Database Changes

Always use Alembic migrations — never modify the schema manually:

```bash
make migrate-create   # Create a new migration
make migrate          # Apply migrations
```
