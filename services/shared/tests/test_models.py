"""Unit tests for ages_common.models.base module."""

from uuid import UUID

from ages_common.models.base import (
    APIResponse,
    EntityBase,
    ErrorResponse,
    PaginatedResponse,
    UserContext,
)


def test_entity_base_defaults() -> None:
    """Verify EntityBase generates UUID and timestamps."""
    entity = EntityBase()

    assert isinstance(entity.id, UUID)
    assert entity.created_at is not None
    assert entity.updated_at is not None


def test_api_response() -> None:
    """Verify APIResponse envelope structure."""
    resp = APIResponse(data={"key": "value"}, message="OK")

    assert resp.success is True
    assert resp.data == {"key": "value"}
    assert resp.message == "OK"


def test_paginated_response() -> None:
    """Verify PaginatedResponse defaults."""
    resp = PaginatedResponse(data=[1, 2, 3], total=100, page=2, page_size=20)

    assert len(resp.data) == 3
    assert resp.total == 100
    assert resp.page == 2
    assert resp.has_next is False


def test_error_response() -> None:
    """Verify ErrorResponse matches RFC 7807."""
    err = ErrorResponse(
        type="https://ages-ai.dev/errors/not_found",
        title="Not Found",
        status=404,
        detail="Repository not found",
        request_id="req-123",
    )
    assert err.status == 404
    assert err.request_id == "req-123"


def test_user_context() -> None:
    """Verify UserContext creation."""
    ctx = UserContext(user_id="user_abc", role="admin", request_id="req-456")

    assert ctx.user_id == "user_abc"
    assert ctx.role == "admin"
    assert ctx.email is None


def test_event_envelope() -> None:
    """Verify EventEnvelope creation and serialization."""
    from ages_common.events.schemas import EventEnvelope, EventTypes

    event = EventEnvelope(
        event_type=EventTypes.REPOSITORY_INDEXED,
        source="embedding-service",
        data={"repository_id": "abc-123", "chunk_count": 42},
    )

    assert event.event_type == "repository.indexed"
    assert event.source == "embedding-service"
    assert event.event_id  # Should auto-generate
    assert event.timestamp  # Should auto-generate

    d = event.model_dump()
    assert d["data"]["chunk_count"] == 42
