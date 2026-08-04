"""FastAPI dependency injection for the Embedding Service."""

from functools import lru_cache

from app.config import EmbeddingSettings, settings
from app.domain.services import EmbeddingService
from app.infrastructure.git_cloner import GitCloner
from app.infrastructure.kafka_publisher import KafkaEventPublisher
from app.infrastructure.openai_embedder import OpenAIEmbedder
from app.infrastructure.postgres_repository import PostgresRepository
from app.infrastructure.qdrant_repository import QdrantRepository
from app.infrastructure.semantic_chunker import SemanticChunker
from app.infrastructure.tree_sitter_parser import TreeSitterParser
from ages_common.database.postgres import PostgresClient
from ages_common.events.producer import KafkaProducer
from ages_common.vector.qdrant import QdrantClient


# ── Singleton clients (initialized on app startup) ──
# These are set by the app lifespan handler in main.py

_postgres_client: PostgresClient | None = None
_qdrant_client: QdrantClient | None = None
_kafka_producer: KafkaProducer | None = None
_embedding_service: EmbeddingService | None = None


def init_clients(
    pg: PostgresClient,
    qdrant: QdrantClient,
    kafka: KafkaProducer,
    service: EmbeddingService,
) -> None:
    """Initialize singleton clients. Called during app startup."""
    global _postgres_client, _qdrant_client, _kafka_producer, _embedding_service
    _postgres_client = pg
    _qdrant_client = qdrant
    _kafka_producer = kafka
    _embedding_service = service


def get_embedding_service() -> EmbeddingService:
    """FastAPI dependency — returns the EmbeddingService singleton."""
    if _embedding_service is None:
        raise RuntimeError("EmbeddingService not initialized")
    return _embedding_service


def get_settings() -> EmbeddingSettings:
    """FastAPI dependency — returns the service configuration."""
    return settings
