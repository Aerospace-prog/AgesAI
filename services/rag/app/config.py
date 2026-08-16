"""RAG service configuration extending the shared BaseServiceSettings."""

from ages_common.config import BaseServiceSettings


class RAGSettings(BaseServiceSettings):
    """Configuration for the AgesAI RAG (Retrieval-Augmented Generation) Service."""

    # ── Service Identity ──
    app_name: str = "ages-ai-rag"
    otel_service_name: str = "ages-ai-rag"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8003

    # ── LLM Settings ──
    default_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-3.5-turbo"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    temperature: float = 0.2
    max_tokens: int = 2048

    # ── Retrieval & Reranking ──
    qdrant_collection_name: str = "code_chunks"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    top_k_vector: int = 20
    top_k_fts: int = 10
    top_k_rerank: int = 5
    rrf_k: int = 60

    # ── Memory ──
    max_memory_messages: int = 10  # Sliding window of past messages
    redis_ttl_seconds: int = 86400  # 24 hours


settings = RAGSettings()
