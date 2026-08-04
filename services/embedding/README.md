# AgesAI Embedding Service

Code repository indexing, parsing, and vector embedding pipeline.

## Architecture

This service follows **Clean Architecture** (Hexagonal/Ports & Adapters):

```
app/
├── api/           ← HTTP Layer (FastAPI routes, schemas)
├── domain/        ← Business Logic (entities, ports, services)
├── infrastructure/← Adapters (PostgreSQL, Qdrant, OpenAI, Kafka, Git)
└── config.py      ← Configuration
```

## Indexing Pipeline

1. **Clone** — `git clone --depth=1` into temp directory
2. **Discover** — Walk file tree, filter by extension/size
3. **Parse** — Tree-sitter extracts AST nodes
4. **Chunk** — AST nodes → CodeChunk entities
5. **Hash** — SHA-256 for incremental indexing
6. **Embed** — OpenAI `text-embedding-3-small` (1536-dim)
7. **Store** — Qdrant vectors + PostgreSQL metadata
8. **Notify** — Kafka `repository.indexed` event

## API Endpoints

| Method | Path | Description |
|:-------|:-----|:------------|
| POST | `/api/v1/repositories/` | Create a repository |
| GET | `/api/v1/repositories/` | List user repositories |
| GET | `/api/v1/repositories/{id}` | Get repository details |
| POST | `/api/v1/repositories/{id}/index` | Start indexing (async) |
| DELETE | `/api/v1/repositories/{id}` | Delete repository |

## Running

```bash
pip install -e "../shared[dev]"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8001
```
