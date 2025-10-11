# Makefile for Crypto News & Sentiment Agent (Linux/Mac)

.PHONY: help up down build test clean logs setup shell lint format

# Default target
help:
	@echo "Crypto News & Sentiment Agent - Linux/Mac Commands"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  up           - Start all services with docker compose"
	@echo "  down         - Stop all services"
	@echo "  build        - Build all Docker images"
	@echo "  setup        - Complete project setup (database + migrations)"
	@echo "  migrate      - Run database migrations"
	@echo "  migrate-create - Create a new migration"
	@echo "  migrate-rollback - Rollback last migration"
	@echo "  migrate-history - Show migration history"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean up containers and volumes"
	@echo "  logs         - Show logs from all services"
	@echo "  shell        - Shell into crypto-agent container"
	@echo "  lint         - Run code linting with ruff"
	@echo "  format       - Format code with black and isort"
	@echo ""
	@echo "For Windows users, use the scripts in the scripts/ directory:"
	@echo "  scripts\\up.bat, scripts\\down.bat, scripts\\setup.bat, etc."
	@echo "  Run 'scripts\\help.bat' for Windows command reference"

# Start all services
up: down
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build all images
build:
	docker compose build

# Complete project setup
setup: init-db migrate
	@echo "Project setup complete!"

# Run database migrations
migrate: up
	@echo "Running database migrations..."
	@sleep 3
	docker compose exec crypto-agent alembic upgrade head

# Create a new migration
migrate-create: up
	@read -p "Enter migration name: " name; \
	docker compose exec crypto-agent alembic revision -m "$$name"

# Rollback last migration
migrate-rollback: up
	@echo "Rolling back last migration..."
	docker compose exec crypto-agent alembic downgrade -1

# Show migration history
migrate-history: up
	docker compose exec crypto-agent alembic history

# Run tests (automatically starts services if needed)
test:
	@echo "Starting services and running tests..."
	docker compose up -d
	@echo "Waiting for services to be ready..."
	sleep 5
	@echo "Running tests..."
	docker compose exec crypto-agent bash -c "cd /app && python -m pytest tests/ -v"

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Show logs
logs:
	docker compose logs -f

# Shell into crypto-agent container
shell:
	docker compose exec crypto-agent bash

# Code quality tools
lint:
	ruff check src/
	ruff check tests/
	black --check src/ tests/

format:
	black src/ tests/
	isort src/ tests/

# =============================================================================
# Internal setup commands (one-time setup, not regular make commands)
# =============================================================================

# Initialize database
init-db:
	docker compose exec crypto-agent bash -c "cd /app/src && python -c 'from database import init_db; init_db()'"

# Setup pgvector extension
setup-pgvector:
	docker compose exec crypto-agent bash -c "cd /app/src && python -c 'from database import setup_pgvector; setup_pgvector()'"

