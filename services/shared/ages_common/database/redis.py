"""Async Redis client for AgesAI services.

Provides connection management, health checks, and typed convenience methods
for common Redis operations (strings, hashes, sorted sets).
"""

import logging
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapping redis-py async interface.

    Usage:
        cache = RedisClient(url="redis://localhost:6379/0")
        await cache.connect()

        await cache.set("key", "value", ttl=300)
        value = await cache.get("key")

        await cache.disconnect()
    """

    def __init__(self, url: str, decode_responses: bool = True) -> None:
        self._url = url
        self._decode_responses = decode_responses
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Initialize the Redis connection."""
        if self._client is not None:
            return

        self._client = aioredis.from_url(
            self._url,
            decode_responses=self._decode_responses,
        )
        logger.info("Redis client connected: %s", self._url)

    async def disconnect(self) -> None:
        """Close the Redis connection gracefully."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Redis client disconnected")

    @property
    def client(self) -> aioredis.Redis:
        """Return the underlying Redis client. Raises if not connected."""
        if self._client is None:
            raise RuntimeError("Redis client not initialized — call connect() first")
        return self._client

    # ── String operations ──

    async def get(self, key: str) -> str | None:
        """Get a string value by key."""
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set a string value with optional TTL (in seconds)."""
        if ttl:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns the number of keys deleted."""
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self.client.exists(key))

    # ── Hash operations ──

    async def hset(self, name: str, mapping: dict[str, Any]) -> None:
        """Set hash fields."""
        await self.client.hset(name, mapping=mapping)  # type: ignore[arg-type]

    async def hget(self, name: str, key: str) -> str | None:
        """Get a hash field value."""
        return await self.client.hget(name, key)

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields."""
        return await self.client.hgetall(name)

    # ── Increment (for rate limiting, counters) ──

    async def incr(self, key: str) -> int:
        """Increment a counter. Returns the new value."""
        return await self.client.incr(key)

    async def expire(self, key: str, ttl: int) -> None:
        """Set a TTL on a key."""
        await self.client.expire(key, ttl)

    # ── Health ──

    async def health_check(self) -> bool:
        """Ping the Redis server."""
        try:
            return await self.client.ping()
        except Exception:
            return False
