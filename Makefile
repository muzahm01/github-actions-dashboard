.PHONY: help build up down logs restart clean test migrate db-shell redis-shell api-shell uv-sync uv-update uv-add uv-lock

# Default target
help:
	@echo "GitHub Actions Dashboard - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial setup (copy .env, install dependencies)"
	@echo "  make build          - Build all Docker images"
	@echo ""
	@echo "UV Package Management:"
	@echo "  make uv-sync        - Install/sync all dependencies"
	@echo "  make uv-update      - Update all dependencies to latest"
	@echo "  make uv-lock        - Update uv.lock file"
	@echo "  make uv-add         - Add a new dependency (e.g., make uv-add PKG=fastapi)"
	@echo "  make uv-clean       - Remove virtual environment and caches"
	@echo ""
	@echo "Docker Management:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - Follow logs from all services"
	@echo "  make logs-api       - Follow API logs"
	@echo "  make logs-worker    - Follow Celery worker logs"
	@echo "  make clean          - Stop services and remove volumes"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make db-reset       - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Development:"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make test-watch     - Run tests in watch mode"
	@echo "  make lint           - Run linters (ruff, mypy)"
	@echo "  make lint-fix       - Run linters with auto-fix"
	@echo "  make format         - Format code with ruff"
	@echo "  make format-check   - Check code formatting without changes"
	@echo "  make api-shell      - Open shell in API container"
	@echo "  make redis-shell    - Open Redis CLI"
	@echo ""
	@echo "Monitoring:"
	@echo "  make prometheus     - Open Prometheus in browser"
	@echo "  make grafana        - Open Grafana in browser"
	@echo "  make health         - Check service health"

# Setup
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env with your actual credentials"; \
	else \
		echo ".env file already exists"; \
	fi
	@cd backend && uv sync
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "  1. Edit .env with your credentials"
	@echo "  2. Run 'make up' to start services"
	@echo "  3. Run 'make migrate' to set up database"

# UV Package Management
uv-sync:
	@echo "Installing dependencies with UV..."
	@cd backend && uv sync
	@echo "Dependencies installed successfully!"

uv-update:
	@echo "Updating all dependencies to latest compatible versions..."
	@cd backend && uv lock --upgrade
	@cd backend && uv sync
	@echo "Dependencies updated! Review uv.lock for changes."

uv-lock:
	@echo "Updating uv.lock file..."
	@cd backend && uv lock
	@echo "Lock file updated!"

uv-add:
	@if [ -z "$(PKG)" ]; then \
		echo "Usage: make uv-add PKG=package-name"; \
		echo "Example: make uv-add PKG=fastapi"; \
		echo "Example: make uv-add PKG='pydantic>=2.0' DEV=1"; \
		exit 1; \
	fi
	@if [ "$(DEV)" = "1" ]; then \
		echo "Adding $(PKG) as development dependency..."; \
		cd backend && uv add --dev $(PKG); \
	else \
		echo "Adding $(PKG) as production dependency..."; \
		cd backend && uv add $(PKG); \
	fi
	@echo "Dependency added successfully!"

uv-remove:
	@if [ -z "$(PKG)" ]; then \
		echo "Usage: make uv-remove PKG=package-name"; \
		echo "Example: make uv-remove PKG=requests"; \
		exit 1; \
	fi
	@echo "Removing $(PKG)..."
	@cd backend && uv remove $(PKG)
	@echo "Dependency removed successfully!"

uv-clean:
	@echo "Cleaning UV cache and virtual environment..."
	@cd backend && rm -rf .venv uv.lock __pycache__ .pytest_cache .ruff_cache .mypy_cache
	@uv cache clean
	@echo "Clean complete! Run 'make uv-sync' to reinstall dependencies."

# Docker Management
build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started. Access points:"
	@echo "  API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f celery-worker

logs-beat:
	docker-compose logs -f celery-beat

clean:
	docker-compose down -v
	@echo "All services stopped and volumes removed"

# Database
migrate:
	docker-compose exec api uv run alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec api uv run alembic revision --autogenerate -m "$$msg"

db-shell:
	docker-compose exec postgres psql -U gha -d github_actions

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		docker-compose exec api uv run alembic upgrade head; \
		echo "Database reset complete"; \
	else \
		echo "Aborted"; \
	fi

# Development
test:
	@echo "Running tests..."
	@cd backend && uv run pytest

test-cov:
	@echo "Running tests with coverage..."
	@cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term --cov-fail-under=85
	@echo ""
	@echo "Coverage report generated in backend/htmlcov/index.html"

test-watch:
	@echo "Running tests in watch mode..."
	@cd backend && uv run pytest -f

test-unit:
	@echo "Running unit tests only..."
	@cd backend && uv run pytest -m unit

test-integration:
	@echo "Running integration tests only..."
	@cd backend && uv run pytest -m integration

test-fast:
	@echo "Running tests in parallel..."
	@cd backend && uv run pytest -n auto

lint:
	@echo "Running linters..."
	@cd backend && uv run ruff check app tests
	@echo "Running type checker..."
	@cd backend && uv run mypy app
	@echo "All checks passed!"

lint-fix:
	@echo "Running linters with auto-fix..."
	@cd backend && uv run ruff check --fix app tests
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	@cd backend && uv run ruff format app tests
	@cd backend && uv run ruff check --fix app tests
	@echo "Code formatted successfully!"

format-check:
	@echo "Checking code formatting..."
	@cd backend && uv run ruff format --check app tests
	@echo "Format check passed!"

quality:
	@echo "Running all quality checks..."
	@make format-check
	@make lint
	@make test
	@echo ""
	@echo "✅ All quality checks passed!"

api-shell:
	docker-compose exec api /bin/bash

redis-shell:
	docker-compose exec redis redis-cli

# Monitoring
prometheus:
	@echo "Opening Prometheus at http://localhost:9090"
	@command -v xdg-open > /dev/null && xdg-open http://localhost:9090 || open http://localhost:9090 || echo "Open http://localhost:9090 in your browser"

grafana:
	@echo "Opening Grafana at http://localhost:3000"
	@echo "Default credentials: admin/admin"
	@command -v xdg-open > /dev/null && xdg-open http://localhost:3000 || open http://localhost:3000 || echo "Open http://localhost:3000 in your browser"

# Health check
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "API not responding"
	@echo ""
	@docker-compose ps
