"""Kafka consumer base class for consuming events from the AgesAI event bus."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from aiokafka import AIOKafkaConsumer

from ages_common.events.schemas import EventEnvelope
from ages_common.exceptions import EventBusError

logger = logging.getLogger(__name__)


class KafkaConsumer(ABC):
    """Abstract async Kafka consumer for processing domain events.

    Subclasses must implement the `handle_event` method.

    Usage:
        class RepositoryEventConsumer(KafkaConsumer):
            async def handle_event(self, event: EventEnvelope) -> None:
                if event.event_type == "repository.created":
                    await self.start_indexing(event.data["repository_id"])

        consumer = RepositoryEventConsumer(
            topics=["repository.events"],
            bootstrap_servers="localhost:9094",
            group_id="embedding-service",
        )
        await consumer.start()
        await consumer.consume()  # Runs indefinitely
        await consumer.stop()
    """

    def __init__(
        self,
        topics: list[str],
        bootstrap_servers: str = "localhost:9094",
        group_id: str = "ages-ai",
        auto_offset_reset: str = "earliest",
    ) -> None:
        self._topics = topics
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._auto_offset_reset = auto_offset_reset
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._consumer is not None:
            return

        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset=self._auto_offset_reset,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            "Kafka consumer started: topics=%s group=%s",
            self._topics, self._group_id,
        )

    async def stop(self) -> None:
        """Stop the Kafka consumer gracefully."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Kafka consumer stopped")

    async def consume(self) -> None:
        """Start consuming messages. Runs until stop() is called.

        Each message is deserialized into an EventEnvelope and passed
        to the abstract handle_event method.
        """
        if self._consumer is None:
            raise EventBusError("Kafka consumer not started — call start() first")

        async for message in self._consumer:
            if not self._running:
                break

            try:
                event = EventEnvelope.model_validate(message.value)
                logger.debug(
                    "Received event: type=%s event_id=%s topic=%s partition=%d offset=%d",
                    event.event_type, event.event_id, message.topic,
                    message.partition, message.offset,
                )
                await self.handle_event(event)
            except Exception as e:
                logger.error(
                    "Error processing event from topic=%s partition=%d offset=%d: %s",
                    message.topic, message.partition, message.offset, str(e),
                    exc_info=True,
                )

    @abstractmethod
    async def handle_event(self, event: EventEnvelope) -> None:
        """Process a single event. Must be implemented by subclasses.

        Args:
            event: The deserialized event envelope.
        """
        ...
