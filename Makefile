# =============================================================================
# Django Matt B2B - Makefile
# =============================================================================
# Run `make help` to see all available commands

.PHONY: help install dev run test lint format migrate shell docker-up docker-down clean

# Default target
.DEFAULT_GOAL := help

# Colors for pretty output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help:
	@echo ""
	@echo "$(BLUE)Django Matt B2B$(RESET) - Available Commands"
	@echo ""
	@echo "$(GREEN)Setup:$(RESET)"
	@echo "  make install        Install production dependencies"
	@echo "  make dev            Install development dependencies"
	@echo "  make setup          Full setup (install + migrate + superuser)"
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@echo "  make run            Run development server"
	@echo "  make shell          Open Django shell (iPython if available)"
	@echo "  make dbshell        Open database shell"
	@echo ""
	@echo "$(GREEN)Database:$(RESET)"
	@echo "  make migrate        Run database migrations"
	@echo "  make migrations     Create new migrations"
	@echo "  make superuser      Create a superuser"
	@echo "  make seed           Seed database with sample data"
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@echo "  make test           Run tests with coverage"
	@echo "  make test-fast      Run tests without coverage"
	@echo "  make test-watch     Run tests in watch mode"
	@echo ""
	@echo "$(GREEN)Code Quality:$(RESET)"
	@echo "  make lint           Run linter (ruff + mypy)"
	@echo "  make format         Format code with ruff"
	@echo "  make check          Run all checks (lint + test)"
	@echo "  make pre-commit     Run pre-commit hooks"
	@echo ""
	@echo "$(GREEN)Docker:$(RESET)"
	@echo "  make docker-up      Start database and Redis"
	@echo "  make docker-down    Stop all containers"
	@echo "  make docker-all     Start all services (including API)"
	@echo "  make docker-dev     Start dev environment with hot reload"
	@echo "  make docker-build   Build Docker images"
	@echo "  make docker-logs    View container logs"
	@echo "  make docker-clean   Remove all containers and volumes"
	@echo ""
	@echo "$(GREEN)Utilities:$(RESET)"
	@echo "  make sync-types     Generate TypeScript types"
	@echo "  make clean          Clean generated files"
	@echo "  make requirements   Export requirements.txt"
	@echo ""

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
install:
	uv sync

dev:
	uv sync --dev

setup: install migrate
	@echo "$(GREEN)Setup complete!$(RESET)"
	@echo "Run 'make superuser' to create an admin user"
	@echo "Run 'make run' to start the development server"

# -----------------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------------
run:
	uv run python manage.py runserver

shell:
	uv run python manage.py shell

dbshell:
	uv run python manage.py dbshell

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
migrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

superuser:
	uv run python manage.py createsuperuser

seed:
	uv run python manage.py seed_data

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------
test:
	uv run pytest -v --cov=apps --cov-report=term-missing --cov-report=html

test-fast:
	uv run pytest -v

test-watch:
	uv run pytest-watch

# -----------------------------------------------------------------------------
# Code Quality
# -----------------------------------------------------------------------------
lint:
	uv run ruff check .
	uv run mypy apps/ --ignore-missing-imports

format:
	uv run ruff format .
	uv run ruff check --fix .

check: lint test
	@echo "$(GREEN)All checks passed!$(RESET)"

pre-commit:
	uv run pre-commit run --all-files

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------
docker-up:
	docker compose up -d db redis
	@echo "$(GREEN)Database and Redis started$(RESET)"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

docker-down:
	docker compose down

docker-all:
	docker compose up -d

docker-dev:
	docker compose --profile dev up

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f

docker-clean:
	docker compose down -v --remove-orphans
	@echo "$(YELLOW)All containers and volumes removed$(RESET)"

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
sync-types:
	uv run python manage.py sync_types --target typescript --output ./types

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/ dist/ *.egg-info/
	@echo "$(GREEN)Cleaned!$(RESET)"

requirements:
	uv pip compile pyproject.toml -o requirements.txt
	uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
	@echo "$(GREEN)Generated requirements.txt and requirements-dev.txt$(RESET)"
