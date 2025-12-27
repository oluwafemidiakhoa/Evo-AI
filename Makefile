.PHONY: help setup dev test lint clean migrate docker-up docker-down docker-logs

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Setup
setup: ## Initial project setup
	@echo "Setting up Evo-AI development environment..."
	cp -n .env.example .env || true
	cp -n backend/.env.example backend/.env || true
	cp -n infrastructure/docker/.env.example infrastructure/docker/.env || true
	cd backend && poetry install
	@echo "Setup complete! Edit .env files with your configuration."

# Development
dev: ## Start development environment with Docker Compose
	cd infrastructure/docker && docker-compose up -d
	@echo "Services starting... Access points:"
	@echo "  - Backend API:    http://localhost:8000/docs"
	@echo "  - Jaeger UI:      http://localhost:16686"
	@echo "  - Grafana:        http://localhost:3001 (admin/admin)"
	@echo "  - Prometheus:     http://localhost:9090"
	@echo "  - MinIO Console:  http://localhost:9001"
	@echo "  - Ray Dashboard:  http://localhost:8265"

dev-backend: ## Run backend locally (outside Docker)
	cd backend && poetry run uvicorn evo_ai.main:app --reload

dev-logs: ## Follow Docker Compose logs
	cd infrastructure/docker && docker-compose logs -f

# Testing
test: ## Run all tests
	cd backend && poetry run pytest

test-unit: ## Run unit tests only
	cd backend && poetry run pytest tests/unit/

test-integration: ## Run integration tests only
	cd backend && poetry run pytest tests/integration/

test-coverage: ## Run tests with coverage report
	cd backend && poetry run pytest --cov=evo_ai --cov-report=html --cov-report=term

# Code Quality
lint: ## Run linters and type checking
	cd backend && poetry run ruff check .
	cd backend && poetry run mypy src/

lint-fix: ## Auto-fix linting issues
	cd backend && poetry run ruff check --fix .
	cd backend && poetry run black src/ tests/

format: ## Format code with black
	cd backend && poetry run black src/ tests/

# Database
migrate: ## Run database migrations
	cd backend && poetry run alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Migration message: " msg; \
	cd backend && poetry run alembic revision --autogenerate -m "$$msg"

migrate-rollback: ## Rollback last migration
	cd backend && poetry run alembic downgrade -1

migrate-history: ## Show migration history
	cd backend && poetry run alembic history

# Docker
docker-up: ## Start all Docker services
	cd infrastructure/docker && docker-compose up -d

docker-down: ## Stop all Docker services
	cd infrastructure/docker && docker-compose down

docker-down-volumes: ## Stop services and remove volumes
	cd infrastructure/docker && docker-compose down -v

docker-restart: ## Restart all Docker services
	cd infrastructure/docker && docker-compose restart

docker-logs: ## Show Docker Compose logs
	cd infrastructure/docker && docker-compose logs -f

docker-build: ## Rebuild Docker images
	cd infrastructure/docker && docker-compose build

docker-ps: ## Show running containers
	cd infrastructure/docker && docker-compose ps

# Cleanup
clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && rm -rf htmlcov .coverage

clean-all: clean docker-down-volumes ## Clean everything including Docker volumes

# Database seeding
seed: ## Seed database with test data
	cd backend && poetry run python -m evo_ai.scripts.seed_data

# Documentation
docs: ## Generate API documentation
	cd backend && poetry run python -m evo_ai.scripts.generate_docs

# Production
build-prod: ## Build production Docker image
	cd backend && docker build --target production -t evo-ai-backend:latest .

# Health checks
health: ## Check service health
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend: DOWN"
	@curl -f http://localhost:9090/-/healthy || echo "Prometheus: DOWN"
	@curl -f http://localhost:16686/ || echo "Jaeger: DOWN"
