---
description: Execute Python development tasks including testing, linting, type checking, and running the backend server.
allowed-tools: [Bash, Edit, Read, Glob, Grep]
---
# Python Development Task: $ARGUMENTS

You are working on the **GitHub Actions Dashboard** backend. Execute the requested Python development task: **$ARGUMENTS**.

## Project Context

- **Location**: `backend/` directory
- **Python Version**: 3.12+
- **Package Manager**: UV (NOT pip)
- **Framework**: FastAPI with async/await
- **Testing**: pytest with 85%+ coverage requirement
- **Linting**: ruff (check + format)
- **Type Checking**: mypy (strict mode)

## Available Commands

### Testing
```bash
cd backend
uv run pytest                              # Run all tests
uv run pytest --cov=app                    # With coverage
uv run pytest --cov=app --cov-report=html  # HTML coverage report
uv run pytest -m unit                      # Unit tests only
uv run pytest -m integration               # Integration tests only
uv run pytest -k "pattern"                 # Run tests matching pattern
uv run pytest -x                           # Stop on first failure
uv run pytest -v                           # Verbose output
```

### Linting & Formatting
```bash
cd backend
uv run ruff check .                # Check for issues
uv run ruff check . --fix          # Auto-fix issues
uv run ruff format .               # Format code
uv run ruff check . --select=ALL   # All rules
```

### Type Checking
```bash
cd backend
uv run mypy app                    # Type check app directory
uv run mypy app tests              # Include tests
uv run mypy app --show-error-codes # Show error codes
```

### Running the Server
```bash
cd backend
uv run uvicorn app.main:app --reload              # Development server
uv run uvicorn app.main:app --host 0.0.0.0        # Listen on all interfaces
uv run uvicorn app.main:app --port 8000 --reload  # Custom port
```

### Dependency Management
```bash
cd backend
uv sync                    # Install all dependencies
uv sync --no-dev           # Production dependencies only
uv add <package>           # Add a dependency
uv add --dev <package>     # Add dev dependency
uv remove <package>        # Remove dependency
uv lock --upgrade          # Upgrade all dependencies
```

### Database Migrations
```bash
cd backend
uv run alembic upgrade head         # Run all migrations
uv run alembic downgrade -1         # Rollback one migration
uv run alembic revision -m "desc"   # Create new migration
uv run alembic history              # Show migration history
uv run alembic current              # Show current revision
```

### Celery Tasks
```bash
cd backend
uv run celery -A app.tasks.celery_app worker --loglevel=info  # Start worker
uv run celery -A app.tasks.celery_app beat --loglevel=info    # Start scheduler
uv run celery -A app.tasks.celery_app inspect active          # View active tasks
```

## Execution Plan

Based on the task **$ARGUMENTS**, follow these steps:

### Step 1: Identify Task Type
Determine what type of task is requested:
- **test/testing**: Run pytest with appropriate flags
- **lint/linting**: Run ruff check and format
- **type/typecheck**: Run mypy
- **run/server**: Start the development server
- **install/deps**: Manage dependencies with UV
- **migrate/migration**: Database migration tasks
- **full/all/quality**: Run lint + type check + tests

### Step 2: Execute Commands
Run the appropriate commands from the backend directory.

### Step 3: Analyze Results
- For tests: Report pass/fail counts, coverage percentage
- For linting: List issues found and fixed
- For type checking: Report any type errors
- For server: Confirm server is running

### Step 4: Fix Issues (if applicable)
If the task involves fixing issues:
1. Read the error messages carefully
2. Locate the problematic files
3. Apply fixes following project conventions
4. Re-run checks to verify fixes

## Code Conventions to Follow

1. **Type Hints**: All functions must have complete type annotations
2. **Async/Await**: Use async for all I/O operations
3. **Dataclasses**: Use `@dataclass(frozen=True)` for immutable value objects
4. **Dependency Injection**: Pass dependencies via constructor
5. **Protocols**: Prefer Protocol over ABC for interfaces
6. **Error Handling**: Use custom exceptions from `app/core/exceptions.py`

## Common Patterns

### Service Class
```python
from dataclasses import dataclass
from typing import Protocol

class MyRepository(Protocol):
    async def get(self, id: int) -> MyEntity: ...

@dataclass
class MyService:
    repo: MyRepository

    async def do_work(self, id: int) -> Result:
        entity = await self.repo.get(id)
        return Result(...)
```

### API Endpoint
```python
from typing import Annotated
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/{id}")
async def get_item(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ItemSchema:
    ...
```

### Test
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.unit
async def test_service_does_work():
    mock_repo = AsyncMock()
    mock_repo.get.return_value = MyEntity(...)

    service = MyService(repo=mock_repo)
    result = await service.do_work(1)

    assert result.status == "success"
    mock_repo.get.assert_called_once_with(1)
```

---
### EXECUTION LOG
(Record commands run and their results below)

