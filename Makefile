.PHONY: help build up down logs restart clean test migrate db-shell redis-shell api-shell

# Default target
help:
	@echo "GitHub Actions Dashboard - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial setup (copy .env, install dependencies)"
	@echo "  make build          - Build all Docker images"
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
	@echo "  make lint           - Run linters (ruff, mypy)"
	@echo "  make format         - Format code with ruff"
	@echo "  make api-shell      - Open shell in API container"
	@echo "  make redis-shell    - Open Redis CLI"
	@echo ""
	@echo "Monitoring:"
	@echo "  make prometheus     - Open Prometheus in browser"
	@echo "  make grafana        - Open Grafana in browser"

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
	cd backend && uv run pytest

test-cov:
	cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term

lint:
	cd backend && uv run ruff check app tests
	cd backend && uv run mypy app

format:
	cd backend && uv run ruff format app tests
	cd backend && uv run ruff check --fix app tests

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
