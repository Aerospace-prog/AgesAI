"""Unit tests for ages_common.exceptions module."""

from ages_common.exceptions import (
    AgesAIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    EmbeddingError,
    EventBusError,
    ExternalServiceError,
    IndexingError,
    LLMError,
    NotFoundError,
    ParsingError,
    RateLimitError,
    RepositoryError,
    ValidationError,
    VectorStoreError,
)


def test_base_exception() -> None:
    """Verify base exception serialization."""
    err = AgesAIError("something broke", details={"key": "value"})
    d = err.to_dict()

    assert d["type"] == "https://ages-ai.dev/errors/internal_error"
    assert d["title"] == "AgesAIError"
    assert d["status"] == 500
    assert d["detail"] == "something broke"
    assert d["details"] == {"key": "value"}


def test_exception_hierarchy_status_codes() -> None:
    """Verify all exceptions map to correct HTTP status codes."""
    cases = [
        (AuthenticationError, 401),
        (AuthorizationError, 403),
        (NotFoundError, 404),
        (ConflictError, 409),
        (ValidationError, 422),
        (RateLimitError, 429),
        (ExternalServiceError, 502),
        (LLMError, 502),
        (VectorStoreError, 502),
        (EmbeddingError, 502),
        (DatabaseError, 500),
        (EventBusError, 500),
        (RepositoryError, 500),
        (ParsingError, 500),
        (IndexingError, 500),
    ]
    for exc_class, expected_status in cases:
        err = exc_class("test")
        assert err.status_code == expected_status, (
            f"{exc_class.__name__}.status_code = {err.status_code}, expected {expected_status}"
        )


def test_exception_inheritance() -> None:
    """Verify the exception hierarchy is correct."""
    assert issubclass(LLMError, ExternalServiceError)
    assert issubclass(ExternalServiceError, AgesAIError)
    assert issubclass(ParsingError, RepositoryError)
    assert issubclass(IndexingError, RepositoryError)
