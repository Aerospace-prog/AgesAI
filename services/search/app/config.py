"""Search service configuration extending the shared BaseServiceSettings."""

from ages_common.config import BaseServiceSettings


class SearchSettings(BaseServiceSettings):
    """Configuration for the AgesAI Search Service."""

    # ── Service Identity ──
    app_name: str = "ages-ai-search"
    otel_service_name: str = "ages-ai-search"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8002

    # ── Embedding (for query vectorization) ──
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # ── Qdrant ──
    qdrant_collection_name: str = "code_chunks"

    # ── Search Defaults ──
    default_limit: int = 10
    max_limit: int = 50
    default_score_threshold: float = 0.35
    hybrid_rrf_k: int = 60  # Reciprocal Rank Fusion constant
    snippet_context_lines: int = 3  # Lines of context around matched code


settings = SearchSettings()
