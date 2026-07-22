# ============================================
# AgesAI Gateway — Makefile
# ============================================

.PHONY: build run test lint clean

BIN := bin/gateway

build: ## Build the gateway binary
	@echo "Building gateway..."
	@CGO_ENABLED=0 go build -o $(BIN) ./cmd/server
	@echo "✓ Built $(BIN)"

run: ## Run the gateway locally
	@go run ./cmd/server

test: ## Run all tests with race detection
	@go test ./... -v -race -coverprofile=coverage.out -covermode=atomic
	@echo "✓ Tests passed"

coverage: test ## Show test coverage
	@go tool cover -html=coverage.out -o coverage.html
	@echo "✓ Coverage report: coverage.html"

lint: ## Run golangci-lint
	@golangci-lint run ./...
	@echo "✓ Lint passed"

clean: ## Remove build artifacts
	@rm -f $(BIN) coverage.out coverage.html
	@echo "✓ Clean"

docker-build: ## Build Docker image
	@docker build -t ages-ai/gateway:latest .
	@echo "✓ Docker image built"
