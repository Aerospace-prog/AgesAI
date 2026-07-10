# ============================================
# AgesAI — Top-Level Makefile
# ============================================
# Usage:
#   make setup    — First-time project setup
#   make dev      — Start full development stack
#   make down     — Stop all containers
#   make test     — Run all tests
#   make lint     — Run all linters
#   make migrate  — Run database migrations
#   make clean    — Clean all build artifacts
# ============================================

.PHONY: help setup dev down test lint build clean migrate seed logs
.DEFAULT_GOAL := help

# ── Variables ──
COMPOSE := docker compose -f infrastructure/docker/docker-compose.yml
COMPOSE_DEV := $(COMPOSE) -f infrastructure/docker/docker-compose.dev.yml
COMPOSE_MON := docker compose -f infrastructure/docker/docker-compose.monitoring.yml
GATEWAY_DIR := gateway
SERVICES_DIR := services
FRONTEND_DIR := frontend

# ── Colors ──
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)AgesAI$(NC) — AI Software Engineering Platform"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ── Setup ──

setup: ## First-time project setup
	@echo "$(BLUE)═══ AgesAI Setup ═══$(NC)"
	@echo "$(YELLOW)Checking prerequisites...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker is required but not installed.$(NC)"; exit 1; }
	@command -v go >/dev/null 2>&1 || { echo "$(RED)Go is required but not installed.$(NC)"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)Python 3 is required but not installed.$(NC)"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "$(RED)Node.js is required but not installed.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All prerequisites found$(NC)"
	@echo ""
	@echo "$(YELLOW)Copying environment file...$(NC)"
	@test -f .env || cp .env.example .env
	@echo "$(GREEN)✓ .env file ready$(NC)"
	@echo ""
	@echo "$(YELLOW)Installing Go dependencies...$(NC)"
	@cd $(GATEWAY_DIR) && go mod download
	@echo "$(GREEN)✓ Go dependencies installed$(NC)"
	@echo ""
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	@cd $(SERVICES_DIR)/shared && pip install -e ".[dev]" -q
	@echo "$(GREEN)✓ Python shared library installed$(NC)"
	@echo ""
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"
	@echo ""
	@echo "$(GREEN)═══ Setup complete! Run 'make dev' to start. ═══$(NC)"

# ── Development ──

dev: ## Start full development stack (all services + infra)
	@echo "$(BLUE)Starting AgesAI development stack...$(NC)"
	$(COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)═══ AgesAI is running ═══$(NC)"
	@echo "  Frontend:    http://localhost:3000"
	@echo "  Gateway:     http://localhost:8000"
	@echo "  API Docs:    http://localhost:8000/api/v1/health"
	@echo "  Qdrant:      http://localhost:6333/dashboard"
	@echo "  MinIO:       http://localhost:9001"
	@echo ""

dev-infra: ## Start only infrastructure (databases, brokers, monitoring)
	@echo "$(BLUE)Starting infrastructure services...$(NC)"
	$(COMPOSE) up -d postgresql redis qdrant kafka minio
	@echo "$(GREEN)✓ Infrastructure ready$(NC)"

dev-monitoring: ## Start monitoring stack (Prometheus, Grafana, Loki, Jaeger)
	@echo "$(BLUE)Starting monitoring stack...$(NC)"
	$(COMPOSE_MON) up -d
	@echo ""
	@echo "$(GREEN)═══ Monitoring is running ═══$(NC)"
	@echo "  Grafana:     http://localhost:3001 (admin/admin)"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Jaeger:      http://localhost:16686"
	@echo ""

down: ## Stop all containers
	@echo "$(YELLOW)Stopping all services...$(NC)"
	$(COMPOSE) down
	$(COMPOSE_MON) down 2>/dev/null || true
	@echo "$(GREEN)✓ All services stopped$(NC)"

down-volumes: ## Stop all containers and remove volumes (DESTRUCTIVE)
	@echo "$(RED)Stopping all services and removing volumes...$(NC)"
	$(COMPOSE) down -v
	$(COMPOSE_MON) down -v 2>/dev/null || true
	@echo "$(GREEN)✓ All services and data removed$(NC)"

restart: ## Restart all containers
	@$(MAKE) down
	@$(MAKE) dev

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

logs-gateway: ## Tail gateway logs
	$(COMPOSE) logs -f gateway

logs-embedding: ## Tail embedding service logs
	$(COMPOSE) logs -f embedding

logs-rag: ## Tail RAG service logs
	$(COMPOSE) logs -f rag

# ── Database ──

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@cd $(GATEWAY_DIR) && go run cmd/migrate/main.go up
	@echo "$(GREEN)✓ Migrations complete$(NC)"

migrate-down: ## Rollback last migration
	@cd $(GATEWAY_DIR) && go run cmd/migrate/main.go down 1

migrate-create: ## Create a new migration (usage: make migrate-create name=create_users)
	@cd $(GATEWAY_DIR) && migrate create -ext sql -dir migrations -seq $(name)

seed: ## Seed database with development data
	@echo "$(BLUE)Seeding database...$(NC)"
	@cd scripts && bash seed.sh
	@echo "$(GREEN)✓ Seed data loaded$(NC)"

# ── Testing ──

test: ## Run all tests
	@echo "$(BLUE)═══ Running All Tests ═══$(NC)"
	@$(MAKE) test-gateway
	@$(MAKE) test-services
	@$(MAKE) test-frontend
	@echo "$(GREEN)═══ All tests passed ═══$(NC)"

test-gateway: ## Run Go gateway tests
	@echo "$(YELLOW)Testing Gateway (Go)...$(NC)"
	@cd $(GATEWAY_DIR) && go test ./... -v -race -coverprofile=coverage.out
	@echo "$(GREEN)✓ Gateway tests passed$(NC)"

test-services: ## Run Python service tests
	@echo "$(YELLOW)Testing Services (Python)...$(NC)"
	@cd $(SERVICES_DIR)/embedding && python -m pytest tests/ -v --cov=app --cov-report=term-missing
	@cd $(SERVICES_DIR)/rag && python -m pytest tests/ -v --cov=app --cov-report=term-missing
	@cd $(SERVICES_DIR)/search && python -m pytest tests/ -v --cov=app --cov-report=term-missing
	@echo "$(GREEN)✓ Service tests passed$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(YELLOW)Testing Frontend (TypeScript)...$(NC)"
	@cd $(FRONTEND_DIR) && npm run test -- --run
	@echo "$(GREEN)✓ Frontend tests passed$(NC)"

# ── Linting ──

lint: ## Run all linters
	@echo "$(BLUE)═══ Running All Linters ═══$(NC)"
	@$(MAKE) lint-gateway
	@$(MAKE) lint-services
	@$(MAKE) lint-frontend
	@echo "$(GREEN)═══ All linters passed ═══$(NC)"

lint-gateway: ## Lint Go code
	@echo "$(YELLOW)Linting Gateway (Go)...$(NC)"
	@cd $(GATEWAY_DIR) && golangci-lint run ./...
	@echo "$(GREEN)✓ Go lint passed$(NC)"

lint-services: ## Lint Python code
	@echo "$(YELLOW)Linting Services (Python)...$(NC)"
	@cd $(SERVICES_DIR) && ruff check .
	@cd $(SERVICES_DIR) && ruff format --check .
	@echo "$(GREEN)✓ Python lint passed$(NC)"

lint-frontend: ## Lint TypeScript code
	@echo "$(YELLOW)Linting Frontend (TypeScript)...$(NC)"
	@cd $(FRONTEND_DIR) && npm run lint
	@echo "$(GREEN)✓ TypeScript lint passed$(NC)"

# ── Build ──

build: ## Build all Docker images
	@echo "$(BLUE)Building all Docker images...$(NC)"
	$(COMPOSE) build
	@echo "$(GREEN)✓ All images built$(NC)"

build-gateway: ## Build gateway Docker image
	@cd $(GATEWAY_DIR) && docker build -t ages-ai/gateway:latest .

build-frontend: ## Build frontend Docker image
	@cd $(FRONTEND_DIR) && docker build -t ages-ai/frontend:latest .

# ── Clean ──

clean: ## Clean all build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@cd $(GATEWAY_DIR) && rm -f coverage.out bin/*
	@cd $(FRONTEND_DIR) && rm -rf .next out node_modules/.cache
	@find $(SERVICES_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find $(SERVICES_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(SERVICES_DIR) -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(NC)"

# ── Utilities ──

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -sf http://localhost:8000/api/v1/health > /dev/null && echo "$(GREEN)✓ Gateway$(NC)" || echo "$(RED)✗ Gateway$(NC)"
	@curl -sf http://localhost:8001/health > /dev/null && echo "$(GREEN)✓ Embedding Service$(NC)" || echo "$(RED)✗ Embedding Service$(NC)"
	@curl -sf http://localhost:8002/health > /dev/null && echo "$(GREEN)✓ Search Service$(NC)" || echo "$(RED)✗ Search Service$(NC)"
	@curl -sf http://localhost:8003/health > /dev/null && echo "$(GREEN)✓ RAG Service$(NC)" || echo "$(RED)✗ RAG Service$(NC)"
	@curl -sf http://localhost:6333/healthz > /dev/null && echo "$(GREEN)✓ Qdrant$(NC)" || echo "$(RED)✗ Qdrant$(NC)"
	@docker compose -f infrastructure/docker/docker-compose.yml exec -T postgresql pg_isready > /dev/null 2>&1 && echo "$(GREEN)✓ PostgreSQL$(NC)" || echo "$(RED)✗ PostgreSQL$(NC)"
	@docker compose -f infrastructure/docker/docker-compose.yml exec -T redis redis-cli ping > /dev/null 2>&1 && echo "$(GREEN)✓ Redis$(NC)" || echo "$(RED)✗ Redis$(NC)"

openapi: ## Generate aggregated OpenAPI spec
	@echo "$(BLUE)Generating OpenAPI spec...$(NC)"
	@bash scripts/generate-openapi.sh
	@echo "$(GREEN)✓ OpenAPI spec generated at docs/api/openapi.yaml$(NC)"

ps: ## Show running containers
	$(COMPOSE) ps
