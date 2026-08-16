"""FastAPI application factory for the AgesAI RAG Service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ages_common.database.postgres import PostgresClient
from ages_common.database.redis import RedisClient
from ages_common.exceptions import AgesAIError
from ages_common.observability.logging import configure_logging
from ages_common.observability.tracing import init_tracing, instrument_fastapi
from ages_common.vector.qdrant import QdrantClient

from app.api.dependencies import init_service
from app.api.v1.routes import router as v1_router
from app.config import settings
from app.domain.services import RAGService
from app.infrastructure.hybrid_retriever import HybridRetrieverAdapter
from app.infrastructure.litellm_provider import LiteLLMProvider
from app.infrastructure.postgres_conversation_repository import PostgresConversationRepository
from app.infrastructure.redis_memory import RedisMemoryAdapter
from app.infrastructure.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown."""

    # ── Startup ──
    logger.info("Starting RAG Service...")

    qdrant = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )
    await qdrant.connect()

    pg = PostgresClient(dsn=settings.database_url)
    await pg.connect()

    redis = RedisClient(redis_url=settings.redis_url)
    await redis.connect()

    # Wire up Clean Architecture adapters
    retriever = HybridRetrieverAdapter(
        qdrant_client=qdrant,
        postgres_client=pg,
        openai_key=settings.openai_api_key,
        collection_name=settings.qdrant_collection_name,
        embedding_model=settings.embedding_model,
        rrf_k=settings.rrf_k,
    )

    reranker = CrossEncoderReranker()
    llm_provider = LiteLLMProvider(
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
    )
    conv_repo = PostgresConversationRepository(client=pg)
    memory = RedisMemoryAdapter(
        redis_client=redis,
        ttl_seconds=settings.redis_ttl_seconds,
        max_messages=settings.max_memory_messages,
    )

    rag_service = RAGService(
        retriever=retriever,
        reranker=reranker,
        llm_provider=llm_provider,
        conversation_repo=conv_repo,
        memory=memory,
        default_model=settings.default_model,
        top_k_retrieve=settings.top_k_vector,
        top_n_rerank=settings.top_k_rerank,
    )

    init_service(rag_service)

    logger.info("RAG Service started successfully")
    yield

    # ── Shutdown ──
    logger.info("Shutting down RAG Service...")
    await redis.disconnect()
    await qdrant.disconnect()
    await pg.disconnect()
    logger.info("RAG Service shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    configure_logging(
        service_name=settings.app_name,
        log_level=settings.log_level.upper(),
        json_format=settings.is_production,
    )

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
        title="AgesAI RAG Service",
        description="Retrieval-Augmented Generation with SSE streaming, hybrid retrieval, and LiteLLM model gateway",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        lifespan=lifespan,
    )

    instrument_fastapi(app)

    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict:
        return {"status": "ready", "service": settings.app_name}

    @app.exception_handler(AgesAIError)
    async def ages_ai_error_handler(request: Request, exc: AgesAIError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    return app


app = create_app()
