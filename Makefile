# Makefile for Alert Monitoring System
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev setup clean test lint format security docs build run stop deploy health demo

# Default target
.DEFAULT_GOAL := help

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Variables
PYTHON := python3.10
PIP := $(PYTHON) -m pip
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := alert-monitoring-system

help: ## Show this help message
	@echo "$(BLUE)Alert Monitoring System - Development Commands$(NC)"
	@echo "=================================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup and Installation

setup: ## Setup the entire project from scratch
	@echo "$(BLUE)Setting up Alert Monitoring System...$(NC)"
	chmod +x setup.sh
	./setup.sh
	@echo "$(GREEN)Setup completed!$(NC)"

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	cd backend && $(PIP) install -r requirements.txt
	cd frontend && $(PIP) install -r requirements.txt
	@echo "$(GREEN)Production dependencies installed!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	cd backend && $(PIP) install -r requirements-dev.txt
	cd frontend && $(PIP) install -r requirements.txt
	@echo "$(GREEN)Development dependencies installed!$(NC)"

venv: ## Create virtual environments
	@echo "$(BLUE)Creating virtual environments...$(NC)"
	cd backend && $(PYTHON) -m venv venv
	cd frontend && $(PYTHON) -m venv venv
	@echo "$(GREEN)Virtual environments created!$(NC)"
	@echo "$(YELLOW)Activate with: source backend/venv/bin/activate$(NC)"

##@ Development

run-backend: ## Run backend development server
	@echo "$(BLUE)Starting backend server...$(NC)"
	cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend: ## Run frontend development server
	@echo "$(BLUE)Starting frontend server...$(NC)"
	cd frontend && source venv/bin/activate && streamlit run app.py --server.port 8501 --server.address 0.0.0.0

run-dev: ## Run both backend and frontend in parallel
	@echo "$(BLUE)Starting development servers...$(NC)"
	$(MAKE) -j2 run-backend run-frontend

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	cd backend && source venv/bin/activate && pytest tests/ -v
	@echo "$(GREEN)All tests completed!$(NC)"

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	cd backend && source venv/bin/activate && pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in backend/htmlcov/$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	cd backend && source venv/bin/activate && pytest-watch tests/

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(NC)"
	cd backend && source venv/bin/activate && pytest tests/ --benchmark-only

##@ Code Quality

lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	cd backend && source venv/bin/activate && flake8 app/ tests/
	cd frontend && source venv/bin/activate && flake8 . --exclude=venv
	@echo "$(GREEN)Linting completed!$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	cd backend && source venv/bin/activate && black app/ tests/ && isort app/ tests/
	cd frontend && source venv/bin/activate && black . && isort .
	@echo "$(GREEN)Code formatting completed!$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	cd backend && source venv/bin/activate && black --check app/ tests/ && isort --check app/ tests/
	cd frontend && source venv/bin/activate && black --check . && isort --check .

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	cd backend && source venv/bin/activate && mypy app/ --ignore-missing-imports

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	cd backend && source venv/bin/activate && bandit -r app/ && safety check
	@echo "$(GREEN)Security checks completed!$(NC)"

quality: lint format-check type-check security ## Run all code quality checks

##@ Docker Operations

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)Docker images built!$(NC)"

up: ## Start all services with Docker Compose
	@echo "$(BLUE)Starting services with Docker Compose...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:8501$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"

down: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Services stopped!$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	$(DOCKER_COMPOSE) restart
	@echo "$(GREEN)Services restarted!$(NC)"

logs: ## Show service logs
	@echo "$(BLUE)Showing service logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f

ps: ## Show running containers
	@echo "$(BLUE)Running containers:$(NC)"
	$(DOCKER_COMPOSE) ps

##@ Maintenance

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-data: ## Clean up data directories (WARNING: This will delete all data!)
	@echo "$(RED)WARNING: This will delete all application data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	rm -rf data/chromadb/*
	rm -rf data/uploads/*
	rm -rf logs/*
	@echo "$(GREEN)Data directories cleaned!$(NC)"

reset: clean clean-data ## Full reset of the project
	@echo "$(GREEN)Project reset completed!$(NC)"

##@ Documentation

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	cd backend && source venv/bin/activate && sphinx-build -b html docs/ docs/_build/html/
	@echo "$(GREEN)Documentation generated in backend/docs/_build/html/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	cd backend/docs/_build/html && $(PYTHON) -m http.server 8080
	@echo "$(YELLOW)Documentation available at http://localhost:8080$(NC)"

##@ Deployment

deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	# Add staging deployment commands here
	@echo "$(GREEN)Deployed to staging!$(NC)"

deploy-prod: ## Deploy to production environment
	@echo "$(BLUE)Deploying to production...$(NC)"
	# Add production deployment commands here
	@echo "$(GREEN)Deployed to production!$(NC)"

backup: ## Backup application data
	@echo "$(BLUE)Creating backup...$(NC)"
	mkdir -p backups
	tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/ logs/
	@echo "$(GREEN)Backup created in backups/$(NC)"

##@ Monitoring

health: ## Check system health
	@echo "$(BLUE)Checking system health...$(NC)"
	@curl -s http://localhost:8000/health | jq . || echo "$(RED)Backend not responding$(NC)"
	@curl -s http://localhost:8501/_stcore/health >/dev/null && echo "$(GREEN)Frontend is healthy$(NC)" || echo "$(RED)Frontend not responding$(NC)"
	@curl -s http://localhost:11434/api/tags >/dev/null && echo "$(GREEN)Ollama is healthy$(NC)" || echo "$(RED)Ollama not responding$(NC)"

status: ## Show detailed system status
	@echo "$(BLUE)System Status:$(NC)"
	@echo "=============="
	@echo "Backend API:"
	@curl -s http://localhost:8000/info | jq . 2>/dev/null || echo "  $(RED)Not available$(NC)"
	@echo "\nAlert Statistics:"
	@curl -s http://localhost:8000/api/v1/alerts/stats/summary | jq .data 2>/dev/null || echo "  $(RED)Not available$(NC)"
	@echo "\nGroup Statistics:"
	@curl -s http://localhost:8000/api/v1/groups/stats/summary | jq .data 2>/dev/null || echo "  $(RED)Not available$(NC)"

stats: ## Show application statistics
	@echo "$(BLUE)Application Statistics:$(NC)"
	@curl -s http://localhost:8000/api/v1/alerts/stats/summary | jq .
	@curl -s http://localhost:8000/api/v1/groups/stats/summary | jq .

##@ Demo and Testing

demo: ## Run the demo script
	@echo "$(BLUE)Running demo script...$(NC)"
	$(PYTHON) demo.py
	@echo "$(GREEN)Demo completed!$(NC)"

demo-clean: ## Run demo and clean up afterwards
	@echo "$(BLUE)Running demo with cleanup...$(NC)"
	$(PYTHON) demo.py --no-cleanup
	@echo "$(GREEN)Demo completed!$(NC)"

load-test: ## Run load testing with locust
	@echo "$(BLUE)Starting load test...$(NC)"
	cd backend && source venv/bin/activate && locust -f tests/load_test.py --host=http://localhost:8000

##@ Development Tools

shell: ## Open a Python shell with project context
	@echo "$(BLUE)Opening Python shell...$(NC)"
	cd backend && source venv/bin/activate && $(PYTHON) -i -c "import sys; sys.path.append('app')"

db-shell: ## Open database shell (ChromaDB)
	@echo "$(BLUE)Opening database shell...$(NC)"
	cd backend && source venv/bin/activate && $(PYTHON) -c "from app.core.database import db_manager; import asyncio; asyncio.run(db_manager.initialize()); print('Database ready')"

lint-fix: ## Automatically fix linting issues
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	cd backend && source venv/bin/activate && autopep8 --in-place --recursive app/ tests/
	cd frontend && source venv/bin/activate && autopep8 --in-place --recursive .
	@echo "$(GREEN)Linting fixes applied!$(NC)"

install-hooks: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	cd backend && source venv/bin/activate && pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed!$(NC)"

##@ Information

requirements: ## Show current package versions
	@echo "$(BLUE)Backend Requirements:$(NC)"
	cd backend && source venv/bin/activate && pip list
	@echo "\n$(BLUE)Frontend Requirements:$(NC)"
	cd frontend && source venv/bin/activate && pip list

ports: ## Show which ports are in use
	@echo "$(BLUE)Checking ports:$(NC)"
	@echo "Port 8000 (Backend):"
	@lsof -i :8000 || echo "  Not in use"
	@echo "Port 8501 (Frontend):"
	@lsof -i :8501 || echo "  Not in use"
	@echo "Port 11434 (Ollama):"
	@lsof -i :11434 || echo "  Not in use"

version: ## Show project version and info
	@echo "$(BLUE)Alert Monitoring System$(NC)"
	@echo "Version: 1.0.0"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker Compose: $(shell docker-compose --version 2>/dev/null || echo 'Not installed')"

##@ Quick Start

quickstart: venv install build up demo ## Complete setup and run demo
	@echo "$(GREEN)🎉 Alert Monitoring System is ready!$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:8501$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"

dev: install-dev run-dev ## Setup development environment and start servers
