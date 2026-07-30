"""Async PostgreSQL connection pool using asyncpg.

Provides a managed connection pool with health checks,
structured logging, and graceful shutdown support.
"""

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class PostgresClient:
    """Async PostgreSQL client wrapping an asyncpg connection pool.

    Usage:
        pg = PostgresClient(dsn="postgresql://user:pass@localhost/db")
        await pg.connect()

        row = await pg.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        rows = await pg.fetch("SELECT * FROM users LIMIT $1", 10)
        await pg.execute("UPDATE users SET name = $1 WHERE id = $2", name, user_id)

        await pg.disconnect()
    """

    def __init__(
        self,
        dsn: str,
        min_size: int = 5,
        max_size: int = 20,
        max_inactive_connection_lifetime: float = 300.0,
    ) -> None:
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._max_inactive = max_inactive_connection_lifetime
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Initialize the connection pool."""
        if self._pool is not None:
            return

        self._pool = await asyncpg.create_pool(
            dsn=self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            max_inactive_connection_lifetime=self._max_inactive,
        )
        logger.info("PostgreSQL pool created (min=%d, max=%d)", self._min_size, self._max_size)

    async def disconnect(self) -> None:
        """Close the connection pool gracefully."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL pool closed")

    @property
    def pool(self) -> asyncpg.Pool:
        """Return the underlying pool. Raises if not connected."""
        if self._pool is None:
            raise RuntimeError("PostgreSQL pool not initialized — call connect() first")
        return self._pool

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """Execute a query and return all rows."""
        return await self.pool.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        """Execute a query and return a single row (or None)."""
        return await self.pool.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Execute a query and return a single value."""
        return await self.pool.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        """Execute a query and return the status string."""
        return await self.pool.execute(query, *args)

    async def executemany(self, query: str, args: list[tuple[Any, ...]]) -> None:
        """Execute a query with multiple parameter sets."""
        await self.pool.executemany(query, args)

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            val = await self.fetchval("SELECT 1")
            return val == 1
        except Exception:
            return False
