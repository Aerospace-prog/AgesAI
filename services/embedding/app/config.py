"""Embedding service configuration extending the shared BaseServiceSettings."""

from ages_common.config import BaseServiceSettings


class EmbeddingSettings(BaseServiceSettings):
    """Configuration for the AgesAI Embedding Service."""

    # ── Service Identity ──
    app_name: str = "ages-ai-embedding"
    otel_service_name: str = "ages-ai-embedding"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8001

    # ── Git ──
    git_clone_timeout: int = 120  # seconds
    git_clone_depth: int = 1
    repo_storage_path: str = "/tmp/ages-ai/repos"

    # ── Parsing ──
    max_file_size_bytes: int = 1_048_576  # 1MB — skip files larger than this
    min_chunk_lines: int = 3
    max_chunk_lines: int = 200

    # ── Embedding ──
    embedding_batch_size: int = 512
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # ── Qdrant ──
    qdrant_collection_name: str = "code_chunks"

    # ── Kafka ──
    kafka_topic_repository_events: str = "repository.events"

    # ── File Filters ──
    excluded_dirs: list[str] = [
        ".git", "node_modules", "vendor", "__pycache__", ".venv", "venv",
        ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist",
        "build", ".next", ".nuxt", "target", "bin", "obj",
    ]
    excluded_extensions: list[str] = [
        ".pyc", ".pyo", ".so", ".o", ".a", ".dylib", ".dll", ".exe",
        ".jar", ".class", ".wasm", ".min.js", ".min.css", ".map",
        ".lock", ".sum", ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".ico", ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4",
        ".pdf", ".zip", ".tar", ".gz", ".bz2", ".7z", ".ds_store",
    ]
    supported_extensions: list[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
        ".kt", ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php",
        ".swift", ".scala", ".r", ".sql", ".sh", ".bash", ".zsh",
        ".yaml", ".yml", ".toml", ".json", ".md", ".txt", ".dockerfile",
    ]


settings = EmbeddingSettings()
