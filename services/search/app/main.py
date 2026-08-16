"""FastAPI application factory for the AgesAI Search Service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ages_common.database.postgres import PostgresClient
from ages_common.exceptions import AgesAIError
from ages_common.observability.logging import configure_logging
from ages_common.observability.tracing import init_tracing, instrument_fastapi
from ages_common.vector.qdrant import QdrantClient

from app.api.dependencies import init_service
from app.api.v1.routes import router as v1_router
from app.config import settings
from app.domain.services import SearchService
from app.infrastructure.openai_embedder import OpenAIQueryEmbedder
from app.infrastructure.postgres_fts import PostgresFullTextSearch
from app.infrastructure.qdrant_search import QdrantSearchAdapter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown."""

    # ── Startup ──
    logger.info("Starting Search Service...")

    # Initialize infrastructure clients
    qdrant = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )
    await qdrant.connect()

    pg = PostgresClient(dsn=settings.database_url)
    await pg.connect()

    # Wire up adapters (Dependency Inversion)
    vector_search = QdrantSearchAdapter(
        client=qdrant,
        collection_name=settings.qdrant_collection_name,
    )
    full_text_search = PostgresFullTextSearch(client=pg)
    query_embedder = OpenAIQueryEmbedder(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )

    # Create domain service
    search_service = SearchService(
        vector_search=vector_search,
        full_text_search=full_text_search,
        query_embedder=query_embedder,
        rrf_k=settings.hybrid_rrf_k,
    )

    init_service(search_service)

    logger.info("Search Service started successfully")
    yield

    # ── Shutdown ──
    logger.info("Shutting down Search Service...")
    await qdrant.disconnect()
    await pg.disconnect()
    logger.info("Search Service shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Configure structured logging
    configure_logging(
        service_name=settings.app_name,
        log_level=settings.log_level.upper(),
        json_format=settings.is_production,
    )

    # Initialize tracing
    if settings.otel_exporter_otlp_endpoint:
        try:
            init_tracing(
                service_name=settings.otel_service_name,
                otlp_endpoint=settings.otel_exporter_otlp_endpoint,
                version=settings.app_version,
                environment=settings.app_env,
            )
        except Exception as e:
            logger.warning("Tracing init failed: %s", str(e))

    app = FastAPI(
        title="AgesAI Search Service",
        description="Semantic and hybrid code search across indexed repositories",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Instrument with OpenTelemetry
    instrument_fastapi(app)

    # Register routes
    app.include_router(v1_router, prefix="/api/v1")

    # Health endpoints
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict:
        return {"status": "ready", "service": settings.app_name}

    # Global exception handler
    @app.exception_handler(AgesAIError)
    async def ages_ai_error_handler(request: Request, exc: AgesAIError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    return app


app = create_app()
