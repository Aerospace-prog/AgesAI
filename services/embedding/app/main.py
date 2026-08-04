"""FastAPI application factory for the AgesAI Embedding Service.

This is the entry point for the service. It:
  1. Configures structured logging
  2. Initializes infrastructure clients (PostgreSQL, Qdrant, Kafka)
  3. Wires up domain services with infrastructure adapters
  4. Registers API routes
  5. Sets up OpenTelemetry instrumentation
  6. Manages graceful startup and shutdown via lifespan
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ages_common.database.postgres import PostgresClient
from ages_common.events.producer import KafkaProducer
from ages_common.exceptions import AgesAIError
from ages_common.observability.logging import configure_logging
from ages_common.observability.tracing import init_tracing, instrument_fastapi
from ages_common.vector.qdrant import QdrantClient

from app.api.dependencies import init_clients
from app.api.v1.routes import router as v1_router
from app.config import settings
from app.domain.services import EmbeddingService
from app.infrastructure.git_cloner import GitCloner
from app.infrastructure.kafka_publisher import KafkaEventPublisher
from app.infrastructure.openai_embedder import OpenAIEmbedder
from app.infrastructure.postgres_repository import PostgresRepository
from app.infrastructure.qdrant_repository import QdrantRepository
from app.infrastructure.semantic_chunker import SemanticChunker
from app.infrastructure.tree_sitter_parser import TreeSitterParser

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown."""

    # ── Startup ──
    logger.info("Starting Embedding Service...")

    # Initialize infrastructure clients
    pg = PostgresClient(dsn=settings.database_url)
    await pg.connect()

    qdrant = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )
    await qdrant.connect()

    kafka = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id="embedding-service",
    )
    try:
        await kafka.start()
    except Exception as e:
        logger.warning("Kafka not available — events will fail: %s", str(e))

    # Wire up adapters (Dependency Inversion)
    repo_port = PostgresRepository(client=pg)
    vector_port = QdrantRepository(
        client=qdrant,
        collection_name=settings.qdrant_collection_name,
        vector_size=settings.embedding_dimensions,
    )
    embedder_port = OpenAIEmbedder(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )
    event_port = KafkaEventPublisher(
        producer=kafka,
        topic=settings.kafka_topic_repository_events,
    )

    # Infrastructure components (not ports)
    git_cloner = GitCloner(
        timeout=settings.git_clone_timeout,
        clone_depth=settings.git_clone_depth,
    )
    parser = TreeSitterParser()
    chunker = SemanticChunker(
        min_lines=settings.min_chunk_lines,
        max_lines=settings.max_chunk_lines,
    )

    # Create domain service
    embedding_service = EmbeddingService(
        repository_port=repo_port,
        vector_store_port=vector_port,
        embedder_port=embedder_port,
        event_publisher_port=event_port,
        git_cloner=git_cloner,
        parser=parser,
        chunker=chunker,
        config=settings,
    )

    # Register singleton clients for dependency injection
    init_clients(pg, qdrant, kafka, embedding_service)

    logger.info("Embedding Service started successfully")
    yield

    # ── Shutdown ──
    logger.info("Shutting down Embedding Service...")
    await kafka.stop()
    await qdrant.disconnect()
    await pg.disconnect()
    logger.info("Embedding Service shutdown complete")


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
            logger.warning("Tracing init failed — continuing without: %s", str(e))

    app = FastAPI(
        title="AgesAI Embedding Service",
        description="Code repository indexing, parsing, and vector embedding pipeline",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Instrument with OpenTelemetry
    instrument_fastapi(app)

    # ── Register Routes ──
    app.include_router(v1_router, prefix="/api/v1")

    # ── Health Endpoints ──
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict:
        return {"status": "ready", "service": settings.app_name}

    # ── Global Exception Handler ──
    @app.exception_handler(AgesAIError)
    async def ages_ai_error_handler(request: Request, exc: AgesAIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    return app


# Module-level app instance for uvicorn
app = create_app()
