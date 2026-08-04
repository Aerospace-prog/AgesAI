# ============================================
# AgesAI Embedding Service — Dockerfile
# ============================================

FROM python:3.12-slim AS base

# Install git (needed for git clone operations)
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy shared library first (layer caching)
COPY services/shared/ /shared/
RUN pip install --no-cache-dir /shared/

# Copy embedding service
COPY services/embedding/pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY services/embedding/ .

# Metadata
LABEL org.opencontainers.image.title="AgesAI Embedding Service"
LABEL org.opencontainers.image.description="Code indexing, parsing, and vector embedding pipeline"
LABEL org.opencontainers.image.source="https://github.com/Aerospace-prog/AgesAI"

# Non-root user
RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
