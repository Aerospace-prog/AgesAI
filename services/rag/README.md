# AgesAI RAG Service

Retrieval-Augmented Generation (RAG) service with SSE streaming chat, hybrid code retrieval, cross-encoder reranking, and LiteLLM model gateway.

## Architecture

Clean Architecture (Hexagonal / Ports & Adapters):

```
app/
├── api/           ← HTTP Layer (FastAPI routes, SSE streaming, schemas)
├── domain/        ← Business Logic (entities, ports, RAGService pipeline)
├── infrastructure/← Adapters (Qdrant/FTS hybrid retriever, CrossEncoder, LiteLLM, Redis, Postgres)
└── config.py      ← Service settings
```

## RAG Pipeline Steps

1. **Query** — Client sends question over `POST /api/v1/chat`
2. **Hybrid Retrieval** — Qdrant vector search + PostgreSQL full-text search fused via Reciprocal Rank Fusion (RRF)
3. **Reranking** — Cross-encoder scoring to filter top N citations
4. **Memory** — Load sliding window past conversation history from Redis / PostgreSQL
5. **Prompt Assembly** — Context-augmented prompt with code citations
6. **Streaming Generation** — LiteLLM model gateway streams completion tokens over SSE
7. **Persistence** — Save messages and citations to PostgreSQL & update Redis session memory

## Endpoints

| Method | Path | Description |
|:-------|:-----|:------------|
| POST | `/api/v1/chat` | RAG Chat with SSE token streaming |
| GET | `/api/v1/conversations` | List user conversation threads |
| GET | `/api/v1/conversations/{id}` | Get conversation history & messages |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation thread |

## Running

```bash
pip install -e "../shared[dev]"
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8003
```
