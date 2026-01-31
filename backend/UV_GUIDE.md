# UV Quick Reference Guide

Quick reference for using UV with the GitHub Actions Dashboard backend.

## 🚀 Getting Started

### Install UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

### Initial Setup
```bash
cd backend

# Install all dependencies
uv sync

# Or use the Makefile
make uv-sync
```

## 📦 Dependency Management

### Adding Dependencies

```bash
# Add production dependency
uv add fastapi
uv add "pydantic>=2.0,<3.0"

# Add development dependency
uv add --dev pytest
uv add --dev ruff

# Using Makefile
make uv-add PKG=httpx
make uv-add PKG=pytest DEV=1
```

### Removing Dependencies

```bash
# Remove a dependency
uv remove package-name

# Using Makefile
make uv-remove PKG=package-name
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade
uv sync

# Update specific package
uv add --upgrade package-name

# Using Makefile
make uv-update
```

## 🔧 Running Commands

### Direct Commands

```bash
# Run any command in the virtual environment
uv run python script.py
uv run pytest
uv run uvicorn app.main:app --reload

# Run Python module
uv run python -m app.main

# Run with arguments
uv run pytest -v -k test_webhook
```

### Using Virtual Environment

```bash
# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Now run commands normally
pytest
python -m app.main

# Deactivate
deactivate
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/unit/api/test_health.py

# Run tests matching pattern
uv run pytest -k "test_webhook"

# Run in parallel
uv run pytest -n auto

# Using Makefile
make test           # All tests
make test-cov       # With coverage
make test-unit      # Unit tests only
make test-fast      # Parallel execution
```

## 🔍 Code Quality

### Linting

```bash
# Check code
uv run ruff check app tests

# Auto-fix issues
uv run ruff check --fix app tests

# Using Makefile
make lint           # Check only
make lint-fix       # With auto-fix
```

### Formatting

```bash
# Format code
uv run ruff format app tests

# Check format without changes
uv run ruff format --check app tests

# Using Makefile
make format         # Format code
make format-check   # Check only
```

### Type Checking

```bash
# Run mypy
uv run mypy app

# Using Makefile
make lint  # Includes mypy
```

## 🗃️ Database

```bash
# Run migrations
uv run alembic upgrade head

# Create migration
uv run alembic revision --autogenerate -m "Add new table"

# Rollback migration
uv run alembic downgrade -1

# Using Makefile
make migrate                          # Apply migrations
make migrate-create MSG="description" # Create migration
```

## 🎯 Common Workflows

### Starting Development

```bash
# 1. Sync dependencies
uv sync

# 2. Start external services
docker-compose up -d postgres redis

# 3. Run migrations
uv run alembic upgrade head

# 4. Start API server
uv run uvicorn app.main:app --reload

# 5. Start Celery worker (separate terminal)
uv run celery -A app.tasks.celery_app worker --loglevel=info
```

### Before Committing

```bash
# Format code
uv run ruff format app tests

# Fix lint issues
uv run ruff check --fix app tests

# Run tests
uv run pytest

# Or use single command
make quality
```

### Updating Project

```bash
# Pull latest changes
git pull

# Sync dependencies (installs new/updated packages)
uv sync

# Run any new migrations
uv run alembic upgrade head
```

## 🐛 Troubleshooting

### Clear Cache and Reinstall

```bash
# Remove everything
rm -rf .venv uv.lock
uv cache clean

# Reinstall
uv sync

# Or use Makefile
make uv-clean
make uv-sync
```

### Lock File Issues

```bash
# Regenerate lock file
uv lock

# Force sync
uv sync --refresh
```

### Import Errors

```bash
# Ensure you're in correct directory
pwd  # Should be .../backend

# Check if dependencies are installed
uv run python -c "import fastapi; print(fastapi.__version__)"

# Resync dependencies
uv sync
```

### Virtual Environment Not Found

```bash
# UV will auto-create .venv on sync
uv sync

# Or manually create
uv venv
```

## 📊 Useful Commands

### Project Information

```bash
# List installed packages
uv pip list

# Show package info
uv pip show fastapi

# Check for dependency tree
uv pip tree

# Verify environment
uv run python -c "import sys; print(sys.executable)"
```

### Lock File

```bash
# Show lock file summary
head -n 50 uv.lock

# Update lock file only (no install)
uv lock

# Update and install
uv lock && uv sync
```

## 🔄 Migration from pip/poetry

### From pip + requirements.txt

```bash
# UV can read requirements.txt
uv pip install -r requirements.txt

# Or convert to pyproject.toml
# Then use uv sync
```

### From poetry

```bash
# UV works with pyproject.toml
# Just run:
uv sync

# Dependencies in [tool.poetry.dependencies]
# are compatible with UV
```

## 💡 Tips and Best Practices

1. **Always use `uv run`** for consistent environment
   ```bash
   uv run pytest  # ✅ Recommended
   pytest         # ❌ Might use wrong environment
   ```

2. **Keep uv.lock in version control**
   - Ensures reproducible builds
   - Commit after dependency changes

3. **Use Makefile shortcuts**
   ```bash
   make test      # Instead of: cd backend && uv run pytest
   make lint      # Instead of: cd backend && uv run ruff check app tests
   ```

4. **Update dependencies regularly**
   ```bash
   make uv-update  # Weekly/monthly
   ```

5. **Use dependency groups**
   ```toml
   [dependency-groups]
   dev = ["pytest", "ruff", "mypy"]
   ```

6. **Pin Python version**
   ```toml
   [project]
   requires-python = ">=3.12"
   ```

## 📚 Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [Migration Guide](https://docs.astral.sh/uv/guides/migration/)
- [pyproject.toml Spec](https://packaging.python.org/en/latest/specifications/pyproject-toml/)

## 🆘 Getting Help

```bash
# UV help
uv --help
uv run --help
uv add --help

# Project-specific help
make help

# Check UV version
uv --version

# Update UV
uv self update
```
