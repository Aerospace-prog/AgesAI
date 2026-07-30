"""Kafka producer base class for publishing events to the AgesAI event bus."""

import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from ages_common.events.schemas import EventEnvelope
from ages_common.exceptions import EventBusError

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Async Kafka producer for publishing domain events.

    Usage:
        producer = KafkaProducer(bootstrap_servers="localhost:9094")
        await producer.start()

        await producer.publish("repository.events", EventEnvelope(
            event_type="repository.indexed",
            source="embedding-service",
            data={"repository_id": "abc123"},
        ))

        await producer.stop()
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9094",
        client_id: str = "ages-ai-producer",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._client_id = client_id
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._producer is not None:
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            client_id=self._client_id,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",  # Wait for all replicas
            enable_idempotence=True,
        )
        await self._producer.start()
        logger.info("Kafka producer started: %s", self._bootstrap_servers)

    async def stop(self) -> None:
        """Stop the Kafka producer gracefully."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def publish(
        self,
        topic: str,
        event: EventEnvelope,
        key: str | None = None,
    ) -> None:
        """Publish an event to a Kafka topic.

        Args:
            topic: The Kafka topic name.
            event: The event envelope to publish.
            key: Optional partition key (e.g., user_id or repository_id).
        """
        if self._producer is None:
            raise EventBusError("Kafka producer not started — call start() first")

        try:
            await self._producer.send_and_wait(
                topic=topic,
                value=event.model_dump(),
                key=key,
            )
            logger.debug(
                "Published event: type=%s topic=%s event_id=%s",
                event.event_type, topic, event.event_id,
            )
        except Exception as e:
            logger.error("Failed to publish event to '%s': %s", topic, str(e))
            raise EventBusError(f"Failed to publish to '{topic}': {e}")
