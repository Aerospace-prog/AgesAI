# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project foundation: monorepo structure, Makefile, Docker Compose, environment configuration
- Go API Gateway with middleware stack (auth, CORS, rate limiting, tracing, logging)
- Shared Python library (`ages_common`) for cross-service utilities
- Embedding Service: repository ingestion, Tree-sitter parsing, OpenAI embeddings, Qdrant storage
- Search Service: semantic vector search, filtered search, result grouping
- RAG Service: streaming AI chat, hybrid retrieval, cross-encoder reranking, conversation memory
- Next.js frontend: dashboard, chat interface, repository management, search
- PostgreSQL schema with 12 tables and full migration suite
- Docker Compose for local development (15+ containers)
- Observability stack: OpenTelemetry, Prometheus, Grafana, Loki, Jaeger
- GitHub Actions CI pipeline
- Professional documentation: ADRs, API docs, deployment guides
