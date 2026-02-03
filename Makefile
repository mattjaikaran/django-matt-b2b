.PHONY: help install dev test lint format migrate run docker-up docker-down clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies with uv"
	@echo "  make dev           - Install dev dependencies"
	@echo "  make run           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code"
	@echo "  make migrate       - Run migrations"
	@echo "  make migrations    - Create new migrations"
	@echo "  make superuser     - Create superuser"
	@echo "  make shell         - Open Django shell"
	@echo "  make docker-up     - Start Docker containers (db + redis)"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-up-all - Start all Docker containers"
	@echo "  make docker-dev    - Start Docker dev environment"
	@echo "  make clean         - Clean up generated files"
	@echo "  make sync-types    - Generate TypeScript types"

# Install dependencies
install:
	uv pip install -e .

# Install dev dependencies
dev:
	uv pip install -e ".[dev]"

# Run development server
run:
	python manage.py runserver

# Run tests
test:
	pytest -v --cov=apps --cov-report=term-missing

# Run linter
lint:
	ruff check .
	mypy apps/

# Format code
format:
	ruff format .
	ruff check --fix .

# Create migrations
migrations:
	python manage.py makemigrations

# Run migrations
migrate:
	python manage.py migrate

# Create superuser
superuser:
	python manage.py createsuperuser

# Docker commands
docker-up:
	docker compose up -d db redis

docker-up-all:
	docker compose up -d

docker-down:
	docker compose down

docker-dev:
	docker compose --profile dev up

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf *.egg-info/

# Generate types for frontend
sync-types:
	python manage.py sync_types --target typescript --output ../frontend/src/types

# Shell
shell:
	python manage.py shell
