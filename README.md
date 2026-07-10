<div align="center">

# 🧠 AgesAI

### AI-Powered Software Engineering Platform

**GitHub Copilot + Cursor + Claude Code + Linear + LangGraph + GitHub Actions + Datadog**
*inside one unified platform.*

[![Go](https://img.shields.io/badge/Go-1.22+-00ADD8?style=flat-square&logo=go&logoColor=white)](https://go.dev/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green?style=flat-square)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](infrastructure/docker/)

</div>

---

## 🎯 What is AgesAI?

AgesAI is an enterprise-grade AI platform that understands your entire codebase and provides intelligent assistance across the software development lifecycle:

| Feature | Description |
|:--------|:------------|
| 🔍 **Semantic Code Search** | Ask questions in natural language — find code by *what it does*, not just by name |
| 💬 **AI Chat (RAG)** | Context-aware conversations about your codebase with real-time streaming |
| 🤖 **Multi-Agent System** | Specialized AI agents for coding, research, planning, and review |
| 🛡️ **Security Analysis** | Automated vulnerability detection, dependency scanning, and OWASP coverage |
| 📊 **Cost Analytics** | Track token usage, compare model costs, and manage AI budgets |
| 📐 **Architecture Diagrams** | Auto-generate Mermaid diagrams from your codebase |
| 🔄 **CI/CD Integration** | GitHub Actions pipelines with automated testing and deployment |
| 📡 **Full Observability** | Distributed tracing, metrics, and log aggregation out of the box |

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Next.js Dashboard                         │
│                   (React + TypeScript + Shadcn/UI)               │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼───────────────────────────────────────┐
│                     Go API Gateway (Chi)                         │
│         Auth │ CORS │ Rate Limit │ Tracing │ Proxy               │
└────┬─────┬──────┬──────┬──────┬──────┬──────┬────────────────────┘
     │     │      │      │      │      │      │
     ▼     ▼      ▼      ▼      ▼      ▼      ▼
 ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
 │Embed │Search│ RAG  │Agent │Review│Planner│Diag │  ← Python/FastAPI
 └──┬───┴──┬──┴──┬───┴──┬───┴──┬───┴──────┴──────┘
    │      │     │      │      │
    ▼      ▼     ▼      ▼      ▼
 ┌──────┬──────┬──────┬──────┬──────┐
 │Qdrant│Postgres│Redis │Kafka │MinIO │  ← Data Layer
 └──────┴──────┴──────┴──────┴──────┘
```

## 🛠 Tech Stack

| Layer | Technologies |
|:------|:-------------|
| **Gateway** | Go 1.22+, Chi Router, OpenTelemetry |
| **AI Services** | Python 3.12+, FastAPI, LangGraph, LangChain, LiteLLM |
| **Frontend** | Next.js 15, React, TypeScript, TailwindCSS, Shadcn/UI, Framer Motion |
| **Databases** | PostgreSQL 16, Redis 7, Qdrant (Vector DB) |
| **Messaging** | Apache Kafka (KRaft mode) |
| **Storage** | MinIO (S3-compatible) |
| **Auth** | Clerk |
| **Observability** | OpenTelemetry, Prometheus, Grafana, Loki, Jaeger |
| **Infrastructure** | Docker, Docker Compose, Kubernetes, Terraform, GitHub Actions |
| **Testing** | Pytest, Go testing, Vitest, Playwright |

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose v2
- [Go 1.22+](https://go.dev/dl/)
- [Python 3.12+](https://python.org/)
- [Node.js 20+](https://nodejs.org/)
- [OpenAI API Key](https://platform.openai.com/) (or [Anthropic](https://console.anthropic.com/))

### Setup

```bash
# Clone the repository
git clone https://github.com/kushagrapandey/ages-ai.git
cd ages-ai

# Configure environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, CLERK keys)

# Start everything
make setup   # Install dependencies (first time only)
make dev     # Start the full stack
```

### Verify

```bash
make health  # Check all services
```

| Service | URL |
|:--------|:----|
| **Dashboard** | [http://localhost:3000](http://localhost:3000) |
| **API Gateway** | [http://localhost:8000](http://localhost:8000/api/v1/health) |
| **Qdrant Dashboard** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) |
| **Grafana** | [http://localhost:3001](http://localhost:3001) (admin/admin) |
| **Jaeger** | [http://localhost:16686](http://localhost:16686) |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) |

## 📸 Screenshots

<!-- Screenshots will be added after frontend implementation -->

*Coming soon — dashboard, chat, search, review, and agent interfaces.*

## 📁 Project Structure

```
ages-ai/
├── gateway/            # Go API Gateway (Chi, middleware, reverse proxy)
├── services/
│   ├── shared/         # Shared Python library (auth, DB, events, telemetry)
│   ├── embedding/      # Repository indexing & vector embedding pipeline
│   ├── search/         # Semantic + hybrid code search
│   ├── rag/            # RAG chat with streaming & conversation memory
│   ├── agent/          # LangGraph multi-agent orchestration
│   └── review/         # AI-powered code review & security scanning
├── frontend/           # Next.js 15 dashboard (Shadcn/UI, TailwindCSS)
├── infrastructure/
│   ├── docker/         # Docker Compose (dev + monitoring)
│   ├── kubernetes/     # K8s manifests (Kustomize)
│   ├── terraform/      # Cloud IaC modules
│   └── monitoring/     # Prometheus, Grafana, Loki, Jaeger, OTel configs
├── docs/               # Architecture, API docs, deployment guides
└── scripts/            # Setup, migration, and utility scripts
```

## 📖 Documentation

| Document | Description |
|:---------|:------------|
| [Architecture](docs/architecture/) | System design, ADRs, diagrams |
| [API Reference](docs/api/) | OpenAPI specification |
| [Database Schema](docs/database/) | ER diagrams, migration guide |
| [Deployment](docs/guides/) | Docker, Kubernetes, production guides |
| [Security](SECURITY.md) | Security policy & vulnerability reporting |
| [Contributing](CONTRIBUTING.md) | Setup, code style, PR process |

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a PR.

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

---

<div align="center">

**Built with ❤️ by [Kushagra Pandey](https://github.com/kushagrapandey)**

</div>
