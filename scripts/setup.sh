#!/usr/bin/env bash
# ============================================
# AgesAI — First-Time Setup Script
# ============================================
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}       AgesAI — Project Setup          ${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

check_cmd() {
    if command -v "$1" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 ($($1 --version 2>&1 | head -1))"
    else
        echo -e "  ${RED}✗${NC} $1 is not installed"
        MISSING=true
    fi
}

MISSING=false
check_cmd docker
check_cmd go
check_cmd python3
check_cmd node
check_cmd npm

if [ "$MISSING" = true ]; then
    echo ""
    echo -e "${RED}Some prerequisites are missing. Please install them and try again.${NC}"
    exit 1
fi

echo ""

# Environment file
echo -e "${YELLOW}Setting up environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "  ${GREEN}✓${NC} Created .env from .env.example"
    echo -e "  ${YELLOW}⚠${NC} Edit .env to add your API keys (OPENAI_API_KEY, CLERK keys)"
else
    echo -e "  ${GREEN}✓${NC} .env already exists"
fi

echo ""

# Start infrastructure
echo -e "${YELLOW}Starting infrastructure services...${NC}"
docker compose -f infrastructure/docker/docker-compose.yml up -d postgresql redis qdrant kafka minio
echo -e "  ${GREEN}✓${NC} Infrastructure containers started"

# Wait for PostgreSQL
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if docker compose -f infrastructure/docker/docker-compose.yml exec -T postgresql pg_isready -U agesai &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL is ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "  ${RED}✗${NC} PostgreSQL failed to start"
        exit 1
    fi
    sleep 1
done

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
for f in gateway/migrations/*.up.sql; do
    echo -e "  Applying: $(basename "$f")"
    docker compose -f infrastructure/docker/docker-compose.yml exec -T postgresql \
        psql -U agesai -d agesai -f "/docker-entrypoint-initdb.d/migrations/$(basename "$f")" 2>/dev/null || true
done
echo -e "  ${GREEN}✓${NC} Migrations applied"

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}       Setup complete!                  ${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Edit ${YELLOW}.env${NC} with your API keys"
echo -e "  2. Run ${YELLOW}make dev${NC} to start all services"
echo -e "  3. Open ${YELLOW}http://localhost:3000${NC} in your browser"
echo ""
