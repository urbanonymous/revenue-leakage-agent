.PHONY: help build up down restart logs clean install-backend install-frontend install dev-backend dev-frontend dev test clear-sandbox shell-backend shell-frontend ps health

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)Revenue Leakage Detection Agent - Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Operations

build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build

up: ## Start all services with Docker Compose
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down

restart: down up ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

ps: ## Show running containers
	docker-compose ps

##@ Development (Local without Docker)

install: install-backend install-frontend ## Install all dependencies locally

install-backend: ## Install backend dependencies with UV
	@echo "$(GREEN)Installing backend dependencies...$(NC)"
	cd backend && uv venv && . .venv/bin/activate && uv pip install -e .

install-frontend: ## Install frontend dependencies with Bun
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	cd frontend && bun install

dev-backend: ## Run backend in development mode (local)
	@echo "$(GREEN)Starting backend development server...$(NC)"
	cd backend && . .venv/bin/activate && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend in development mode (local)
	@echo "$(GREEN)Starting frontend development server...$(NC)"
	cd frontend && bun run dev

dev: ## Run both backend and frontend in development mode
	@echo "$(GREEN)Starting development servers...$(NC)"
	@echo "Run 'make dev-backend' in one terminal and 'make dev-frontend' in another"

##@ Investigation & Testing

investigate: ## Run full revenue investigation
	@echo "$(GREEN)Running investigation...$(NC)"
	curl -X POST http://localhost:8000/api/investigate | jq

health: ## Check health of backend API
	@echo "$(GREEN)Checking backend health...$(NC)"
	curl http://localhost:8000/api/health | jq

test-api: ## Test all API endpoints
	@echo "$(GREEN)Testing API endpoints...$(NC)"
	@echo "\n$(BLUE)Health Check:$(NC)"
	curl -s http://localhost:8000/ | jq
	@echo "\n$(BLUE)Running Investigation:$(NC)"
	curl -s -X POST http://localhost:8000/api/investigate | jq '.summary'
	@echo "\n$(BLUE)Getting Sandbox Stats:$(NC)"
	curl -s http://localhost:8000/api/sandbox/stats | jq

##@ Sandbox Management

clear-sandbox: ## Clear all sandbox files
	@echo "$(YELLOW)Clearing sandbox...$(NC)"
	curl -X DELETE http://localhost:8000/api/sandbox/clear | jq

sandbox-stats: ## Show sandbox statistics
	@echo "$(GREEN)Sandbox statistics:$(NC)"
	curl -s http://localhost:8000/api/sandbox/stats | jq

audit-log: ## View audit log
	@echo "$(GREEN)Audit log:$(NC)"
	curl -s http://localhost:8000/api/audit-log | jq

##@ Shell Access

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

##@ Cleanup

clean: down ## Stop services and remove containers, networks, volumes
	@echo "$(RED)Cleaning up Docker resources...$(NC)"
	docker-compose down -v --remove-orphans
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: clean ## Deep clean - remove images, containers, volumes, build cache
	@echo "$(RED)Performing deep clean...$(NC)"
	docker-compose down -v --rmi all --remove-orphans
	rm -rf backend/.venv
	rm -rf backend/__pycache__
	rm -rf backend/src/__pycache__
	rm -rf backend/src/**/__pycache__
	rm -rf frontend/node_modules
	rm -rf frontend/dist
	@echo "$(GREEN)Deep clean complete!$(NC)"

clean-sandbox-files: ## Remove sandbox JSON files
	@echo "$(YELLOW)Removing sandbox files...$(NC)"
	rm -f sandbox/*.json
	echo "[]" > sandbox/make_good_invoices.json
	echo "[]" > sandbox/credit_memos.json
	echo "[]" > sandbox/plan_amendments.json
	echo "[]" > sandbox/audit_log.json
	@echo "$(GREEN)Sandbox files reset!$(NC)"

##@ Quick Actions

rebuild: clean build up ## Rebuild everything from scratch

quick-start: build up logs ## Build, start, and show logs

stop: down ## Alias for 'down' - stop all services

status: ps ## Alias for 'ps' - show container status

##@ Documentation

docs: ## Open API documentation in browser
	@echo "$(GREEN)Opening API documentation...$(NC)"
	open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Please open http://localhost:8000/docs manually"

frontend: ## Open frontend in browser
	@echo "$(GREEN)Opening frontend...$(NC)"
	open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Please open http://localhost:3000 manually"

