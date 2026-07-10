# Contributing to AgesAI

Thank you for your interest in contributing to AgesAI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Architecture Decisions](#architecture-decisions)

## Development Setup

### Prerequisites

| Tool | Version | Check |
|:-----|:--------|:------|
| Docker | 24+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Go | 1.22+ | `go version` |
| Python | 3.12+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |

### Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/ages-ai.git
cd ages-ai

# 2. Setup
make setup

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, CLERK keys)

# 4. Start development
make dev

# 5. Verify
make health
```

## Project Structure

```
ages-ai/
├── gateway/          # Go API Gateway
├── services/         # Python microservices
│   ├── shared/       # Shared library (ages_common)
│   ├── embedding/    # Embedding Service
│   ├── rag/          # RAG Service
│   ├── search/       # Search Service
│   ├── agent/        # Agent Service
│   └── review/       # Review Service
├── frontend/         # Next.js Dashboard
├── infrastructure/   # Docker, K8s, Terraform
└── docs/             # Documentation
```

## Development Workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make changes** following the code style guidelines.

3. **Write tests** for your changes.

4. **Run checks locally**:
   ```bash
   make lint    # Run all linters
   make test    # Run all tests
   ```

5. **Commit** using conventional commits (see below).

6. **Push** and create a Pull Request.

## Code Style

### Go (Gateway)
- Follow [Effective Go](https://go.dev/doc/effective_go)
- Use `golangci-lint` (config in `.golangci.yml`)
- Use `slog` for structured logging
- Interfaces in the consumer package

### Python (Services)
- Follow PEP 8, enforced by `ruff`
- Type hints on all function signatures
- Pydantic models for all API schemas
- Async/await for all I/O operations
- Clean Architecture: `api/ → domain/ → infrastructure/`

### TypeScript (Frontend)
- Strict TypeScript mode
- ESLint + Prettier
- Functional components with hooks
- Server Components by default, `"use client"` only when needed

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|:-----|:------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Code refactoring (no behavior change) |
| `test` | Adding or updating tests |
| `ci` | CI/CD pipeline changes |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |

### Scopes

`gateway`, `embedding`, `rag`, `search`, `agent`, `review`, `frontend`, `infra`, `docs`

### Examples

```
feat(rag): add cross-encoder reranking to retrieval pipeline
fix(gateway): handle nil JWT claims in auth middleware
docs: add ADR for vector database selection
test(search): add filtered search integration tests
ci: add Trivy container scanning to security workflow
```

## Pull Request Process

1. **Title** follows commit convention: `feat(scope): description`
2. **Description** explains what and why (not just how)
3. **Tests** pass (CI will verify)
4. **Documentation** is updated if behavior changes
5. **One approval** required from a maintainer
6. **Squash merge** to keep history clean

## Architecture Decisions

Major architectural decisions are documented as ADRs in `docs/architecture/adr/`.

Before proposing a significant architectural change:
1. Read existing ADRs to understand past decisions
2. Create a new ADR using the template at `docs/architecture/adr/template.md`
3. Open a PR with the ADR for discussion before implementing
