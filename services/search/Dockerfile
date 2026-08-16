# ============================================
# AgesAI Search Service — Dockerfile
# ============================================

FROM python:3.12-slim AS base

WORKDIR /app

# Copy shared library first (layer caching)
COPY services/shared/ /shared/
RUN pip install --no-cache-dir /shared/

# Copy search service
COPY services/search/pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY services/search/ .

# Metadata
LABEL org.opencontainers.image.title="AgesAI Search Service"
LABEL org.opencontainers.image.description="Semantic and hybrid code search"
LABEL org.opencontainers.image.source="https://github.com/Aerospace-prog/AgesAI"

# Non-root user
RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
