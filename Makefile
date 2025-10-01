# Makefile for Crypto News & Sentiment Agent (Linux/Mac)

.PHONY: help up down build test clean logs setup process-s3 fetch-coingecko test-api

# Default target
help:
	@echo "Crypto News & Sentiment Agent - Linux/Mac Commands"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  up           - Start all services with docker compose"
	@echo "  down         - Stop all services"
	@echo "  build        - Build all Docker images"
	@echo "  setup        - Complete project setup (database + pgvector)"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean up containers and volumes"
	@echo "  logs         - Show logs from all services"
	@echo "  logs-app     - Show logs from crypto-agent service only"
	@echo "  shell        - Shell into crypto-agent container"
	@echo "  process-s3   - Process S3 PDFs and store in database"
	@echo "  fetch-coingecko - Fetch latest crypto news from CoinGecko API"
	@echo "  analyze-sentiment - Analyze sentiment for all articles using Bedrock"
	@echo "  test-api     - Test API endpoints"
	@echo ""
	@echo "Python dependency management (uv):"
	@echo "  install      - Install Python dependencies"
	@echo "  export-req   - Export requirements.txt from pyproject.toml"
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
setup: init-db setup-pgvector
	@echo "Project setup complete!"

# Initialize database
init-db:
	docker compose exec crypto-agent bash -c "cd /app && python -c 'from src.database import init_db; init_db()'"

# Setup pgvector extension
setup-pgvector:
	docker compose exec crypto-agent bash -c "cd /app && python -c 'from src.database import setup_pgvector; setup_pgvector()'"

# Run tests
test:
	docker compose exec crypto-agent bash -c "cd /app && python -m pytest tests/ -v"

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Show logs
logs:
	docker compose logs -f

# Show crypto-agent logs only
logs-app:
	docker compose logs -f crypto-agent

# Shell into crypto-agent container
shell:
	docker compose exec crypto-agent bash

# Install Python dependencies
install:
	uv pip install -e .

# Generate requirements.txt from pyproject.toml (if needed for compatibility)
export-req:
	uv export --format requirements-txt > requirements.txt

# Process S3 PDFs and store in database
process-s3:
	docker compose exec crypto-agent python -c "from src.services.s3_processor import process_s3_pdfs; process_s3_pdfs()"

# Fetch latest crypto news from CoinGecko API
fetch-coingecko:
	docker compose exec crypto-agent python -c "import asyncio; from src.services.coingecko_service import fetch_latest_news; asyncio.run(fetch_latest_news())"

# Analyze sentiment for all articles
analyze-sentiment:
	docker compose exec crypto-agent python -c "from src.services.sentiment_analyzer import analyze_all_articles; analyze_all_articles()"

# Run FastAPI development server locally
run-local:
	cd src && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Code quality tools
lint:
	ruff check src/
	ruff check tests/

format:
	black src/ tests/
	isort src/ tests/

# Test API endpoints
test-api:
	@echo "Testing API endpoints..."
	@echo "Health check:"
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo "\nNews articles:"
	@curl -s http://localhost:8000/api/news/ | python3 -m json.tool
	@echo "\nSentiment analysis:"
	@curl -s http://localhost:8000/api/sentiment/ | python3 -m json.tool

