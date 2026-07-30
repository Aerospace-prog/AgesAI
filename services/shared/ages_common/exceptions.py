"""Domain exception hierarchy for AgesAI services.

All custom exceptions inherit from AgesAIError, enabling uniform error handling
across services. Each exception maps to an HTTP status code for API layer translation.
"""

from typing import Any


class AgesAIError(Exception):
    """Base exception for all AgesAI domain errors."""

    status_code: int = 500
    error_type: str = "internal_error"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": f"https://ages-ai.dev/errors/{self.error_type}",
            "title": self.__class__.__name__,
            "status": self.status_code,
            "detail": self.message,
            **({"details": self.details} if self.details else {}),
        }


# ── Authentication & Authorization ──

class AuthenticationError(AgesAIError):
    """Raised when authentication fails (invalid/expired token)."""
    status_code = 401
    error_type = "authentication_error"


class AuthorizationError(AgesAIError):
    """Raised when the user lacks permission for the requested operation."""
    status_code = 403
    error_type = "authorization_error"


# ── Resource Errors ──

class NotFoundError(AgesAIError):
    """Raised when a requested resource does not exist."""
    status_code = 404
    error_type = "not_found"


class ConflictError(AgesAIError):
    """Raised when a resource already exists or a conflicting operation is attempted."""
    status_code = 409
    error_type = "conflict"


class ValidationError(AgesAIError):
    """Raised when request data fails domain validation."""
    status_code = 422
    error_type = "validation_error"


# ── Rate Limiting ──

class RateLimitError(AgesAIError):
    """Raised when a user exceeds rate limits."""
    status_code = 429
    error_type = "rate_limit_exceeded"


# ── External Service Errors ──

class ExternalServiceError(AgesAIError):
    """Raised when an external service (LLM, Qdrant, etc.) fails."""
    status_code = 502
    error_type = "external_service_error"


class LLMError(ExternalServiceError):
    """Raised when an LLM API call fails."""
    error_type = "llm_error"


class VectorStoreError(ExternalServiceError):
    """Raised when vector database operations fail."""
    error_type = "vector_store_error"


class EmbeddingError(ExternalServiceError):
    """Raised when embedding generation fails."""
    error_type = "embedding_error"


# ── Infrastructure Errors ──

class DatabaseError(AgesAIError):
    """Raised when a database operation fails."""
    status_code = 500
    error_type = "database_error"


class EventBusError(AgesAIError):
    """Raised when Kafka event publishing/consuming fails."""
    status_code = 500
    error_type = "event_bus_error"


# ── Pipeline Errors ──

class RepositoryError(AgesAIError):
    """Raised when repository operations (clone, parse, index) fail."""
    status_code = 500
    error_type = "repository_error"


class ParsingError(RepositoryError):
    """Raised when code parsing fails."""
    error_type = "parsing_error"


class IndexingError(RepositoryError):
    """Raised when indexing pipeline fails."""
    error_type = "indexing_error"
