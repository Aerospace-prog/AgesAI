"""Redis adapter implementing MemoryPort for conversation history caching."""

import json
import logging
from uuid import UUID

from app.domain.ports import MemoryPort
from ages_common.database.redis import RedisClient

logger = logging.getLogger(__name__)


class RedisMemoryAdapter(MemoryPort):
    """Redis sliding window memory for fast prompt assembly."""

    def __init__(self, redis_client: RedisClient, ttl_seconds: int = 86400, max_messages: int = 10) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds
        self._max = max_messages

    def _key(self, conversation_id: UUID) -> str:
        return f"rag:memory:{conversation_id}"

    async def get_memory(self, conversation_id: UUID) -> list[dict[str, str]]:
        key = self._key(conversation_id)
        val = await self._redis.get(key)
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    async def append_memory(self, conversation_id: UUID, user_msg: str, assistant_msg: str) -> None:
        history = await self.get_memory(conversation_id)
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})

        # Keep sliding window
        if len(history) > self._max:
            history = history[-self._max :]

        key = self._key(conversation_id)
        await self._redis.set(key, json.dumps(history), ttl=self._ttl)
