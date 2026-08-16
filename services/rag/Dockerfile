# ============================================
# AgesAI RAG Service — Dockerfile
# ============================================

FROM python:3.12-slim AS base

WORKDIR /app

# Copy shared library first (layer caching)
COPY services/shared/ /shared/
RUN pip install --no-cache-dir /shared/

# Copy RAG service
COPY services/rag/pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY services/rag/ .

# Metadata
LABEL org.opencontainers.image.title="AgesAI RAG Service"
LABEL org.opencontainers.image.description="RAG Chat Service with SSE Streaming and LiteLLM"
LABEL org.opencontainers.image.source="https://github.com/Aerospace-prog/AgesAI"

# Non-root user
RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
