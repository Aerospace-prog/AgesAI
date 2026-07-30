"""Event envelope schema for Kafka messages.

All Kafka events follow a standard envelope format for consistency
and debuggability across the event bus.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import Field

from ages_common.models.base import AgesBaseModel


class EventEnvelope(AgesBaseModel):
    """Standard event envelope wrapping all Kafka messages.

    Attributes:
        event_id: Unique identifier for this event instance.
        event_type: Dot-notation event type (e.g., "repository.indexed").
        source: Service that produced the event.
        timestamp: When the event was created (ISO 8601).
        data: The event-specific payload.
        metadata: Optional metadata (trace IDs, user context, etc.).
    """

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    source: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    data: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Well-Known Event Types ──

class EventTypes:
    """Constants for all AgesAI event types."""

    # Repository lifecycle
    REPOSITORY_CREATED = "repository.created"
    REPOSITORY_INDEXED = "repository.indexed"
    REPOSITORY_DELETED = "repository.deleted"
    REPOSITORY_FAILED = "repository.failed"

    # Chat / RAG
    CHAT_MESSAGE_SENT = "chat.message.sent"
    CHAT_RESPONSE_COMPLETE = "chat.response.complete"

    # Agent
    AGENT_RUN_STARTED = "agent.run.started"
    AGENT_RUN_COMPLETED = "agent.run.completed"
    AGENT_RUN_FAILED = "agent.run.failed"

    # Review
    REVIEW_REQUESTED = "review.requested"
    REVIEW_COMPLETED = "review.completed"

    # User
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
