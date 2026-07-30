"""Base configuration for all AgesAI microservices using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base settings class inherited by every AgesAI microservice.

    Values are loaded from environment variables with the given prefix.
    A .env file is automatically loaded if present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ──
    app_name: str = "ages-ai-service"
    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "debug"

    # ── Database ──
    database_url: str = "postgresql://agesai:dev_db_pass_placeholder@localhost:5432/agesai"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── Qdrant ──
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # ── Kafka ──
    kafka_bootstrap_servers: str = "localhost:9094"
    kafka_group_id: str = "ages-ai"

    # ── OpenTelemetry ──
    otel_exporter_otlp_endpoint: str = "localhost:4317"
    otel_service_name: str = "ages-ai-service"

    # ── LLM ──
    openai_api_key: str = ""
    default_chat_model: str = "gpt-4o"
    default_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
