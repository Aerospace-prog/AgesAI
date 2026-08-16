# AgesAI Search Service

Semantic and hybrid code search across indexed repositories.

## Architecture

Clean Architecture (Hexagonal/Ports & Adapters):

```
app/
├── api/           ← HTTP Layer (FastAPI routes, schemas)
├── domain/        ← Business Logic (entities, ports, services)
├── infrastructure/← Adapters (Qdrant, PostgreSQL FTS, OpenAI)
└── config.py      ← Configuration
```

## Search Modes

### Semantic Search (`POST /api/v1/search/`)
Embeds the query with OpenAI → cosine similarity search in Qdrant → returns results grouped by file.

### Hybrid Search (`POST /api/v1/search/hybrid`)
Parallel vector + full-text search → **Reciprocal Rank Fusion (RRF)** → merged ranked results.

## API Endpoints

| Method | Path | Description |
|:-------|:-----|:------------|
| POST | `/api/v1/search/` | Semantic (vector) code search |
| POST | `/api/v1/search/hybrid` | Hybrid search (vector + FTS + RRF) |

## Filters

All search endpoints support:
- `repository_ids` — Filter by repository
- `languages` — Filter by programming language (python, typescript, go, etc.)
- `chunk_types` — Filter by code element type (function, class, method, etc.)
- `limit` — Maximum results (default: 10, max: 50)
- `score_threshold` — Minimum similarity score

## Running

```bash
pip install -e "../shared[dev]"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8002
```
