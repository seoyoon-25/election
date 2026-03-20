# Campaign Operations OS - Development Commands
.PHONY: help up down build logs logs-backend logs-frontend shell db-shell migrate test lint clean frontend-shell frontend-install

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Docker commands
up: ## Start all services
	docker-compose up -d

up-build: ## Build and start all services
	docker-compose up -d --build

down: ## Stop all services
	docker-compose down

down-v: ## Stop all services and remove volumes
	docker-compose down -v

build: ## Build Docker images
	docker-compose build

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs only
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	docker-compose logs -f frontend

restart: ## Restart all services
	docker-compose restart

restart-backend: ## Restart backend only
	docker-compose restart backend

restart-frontend: ## Restart frontend only
	docker-compose restart frontend

# Shell access
shell: ## Open a shell in the backend container
	docker-compose exec backend bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U campaign_os -d campaign_os

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

# Database
migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"

migrate-down: ## Rollback last migration
	docker-compose exec backend alembic downgrade -1

# Testing
test: ## Run tests
	docker-compose exec backend pytest tests/ -v

test-cov: ## Run tests with coverage
	docker-compose exec backend pytest tests/ -v --cov=app --cov-report=html

# Linting
lint: ## Run linters
	docker-compose exec backend ruff check app/ tests/

lint-fix: ## Run linters and fix issues
	docker-compose exec backend ruff check --fix app/ tests/

format: ## Format code
	docker-compose exec backend ruff format app/ tests/

# Frontend
frontend-shell: ## Open a shell in the frontend container
	docker-compose exec frontend sh

frontend-install: ## Install frontend dependencies locally
	cd frontend && npm install

# Cleanup
clean: ## Remove all containers, images, and volumes
	docker-compose down -v --rmi local
	docker system prune -f
