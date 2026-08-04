"""Kafka event publisher adapter — implements EventPublisherPort."""

import logging
from uuid import UUID

from app.domain.ports import EventPublisherPort
from ages_common.events.producer import KafkaProducer
from ages_common.events.schemas import EventEnvelope, EventTypes

logger = logging.getLogger(__name__)


class KafkaEventPublisher(EventPublisherPort):
    """Kafka adapter for publishing domain events.

    Implements the EventPublisherPort interface.
    """

    def __init__(self, producer: KafkaProducer, topic: str = "repository.events") -> None:
        self._producer = producer
        self._topic = topic

    async def publish_repository_indexed(self, repository_id: UUID, chunk_count: int) -> None:
        """Publish a repository.indexed event."""
        event = EventEnvelope(
            event_type=EventTypes.REPOSITORY_INDEXED,
            source="embedding-service",
            data={
                "repository_id": str(repository_id),
                "chunk_count": chunk_count,
            },
        )
        await self._producer.publish(
            topic=self._topic,
            event=event,
            key=str(repository_id),
        )

    async def publish_repository_failed(self, repository_id: UUID, error: str) -> None:
        """Publish a repository.failed event."""
        event = EventEnvelope(
            event_type=EventTypes.REPOSITORY_FAILED,
            source="embedding-service",
            data={
                "repository_id": str(repository_id),
                "error": error,
            },
        )
        await self._producer.publish(
            topic=self._topic,
            event=event,
            key=str(repository_id),
        )
