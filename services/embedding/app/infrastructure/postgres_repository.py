"""PostgreSQL repository adapter — implements RepositoryPort."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.domain.entities import IndexedFile, Repository, RepositorySource, RepositoryStatus
from app.domain.ports import RepositoryPort
from ages_common.database.postgres import PostgresClient

logger = logging.getLogger(__name__)


class PostgresRepository(RepositoryPort):
    """PostgreSQL adapter for repository persistence.

    Implements the RepositoryPort interface.
    """

    def __init__(self, client: PostgresClient) -> None:
        self._db = client

    async def create(self, repository: Repository) -> Repository:
        """Insert a new repository record."""
        row = await self._db.fetchrow(
            """
            INSERT INTO repositories (id, user_id, name, url, source, default_branch, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            repository.id, repository.user_id, repository.name,
            repository.url, repository.source.value, repository.default_branch,
            repository.status.value,
        )
        if row:
            return self._row_to_entity(row)
        return repository

    async def get_by_id(self, repository_id: UUID) -> Repository | None:
        """Fetch a repository by ID."""
        row = await self._db.fetchrow(
            "SELECT * FROM repositories WHERE id = $1", repository_id
        )
        return self._row_to_entity(row) if row else None

    async def get_by_user_id(self, user_id: str) -> list[Repository]:
        """Fetch all repositories for a user."""
        rows = await self._db.fetch(
            "SELECT * FROM repositories WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
        return [self._row_to_entity(row) for row in rows]

    async def update_status(
        self, repository_id: UUID, status: RepositoryStatus, error_message: str | None = None,
    ) -> None:
        """Update repository status."""
        await self._db.execute(
            """
            UPDATE repositories
            SET status = $2, error_message = $3, updated_at = $4
            WHERE id = $1
            """,
            repository_id, status.value, error_message, datetime.now(UTC),
        )

    async def update_stats(
        self, repository_id: UUID, file_count: int, chunk_count: int, embedding_count: int,
    ) -> None:
        """Update repository indexing statistics."""
        await self._db.execute(
            """
            UPDATE repositories
            SET file_count = $2, chunk_count = $3, embedding_count = $4,
                last_indexed_at = $5, updated_at = $5
            WHERE id = $1
            """,
            repository_id, file_count, chunk_count, embedding_count, datetime.now(UTC),
        )

    async def delete(self, repository_id: UUID) -> None:
        """Delete a repository and all cascading data."""
        await self._db.execute("DELETE FROM repositories WHERE id = $1", repository_id)
        logger.info("Deleted repository %s", repository_id)

    async def save_indexed_files(self, files: list[IndexedFile]) -> None:
        """Bulk insert indexed file records."""
        args = [
            (f.id, f.repository_id, f.file_path, f.language, f.content_hash,
             f.chunk_count, f.line_count, f.size_bytes, f.indexed_at)
            for f in files
        ]
        await self._db.executemany(
            """
            INSERT INTO indexed_files (id, repository_id, file_path, language, content_hash,
                                       chunk_count, line_count, size_bytes, indexed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT DO NOTHING
            """,
            args,
        )

    def _row_to_entity(self, row: object) -> Repository:
        """Convert a database row to a Repository entity."""
        r = dict(row)  # type: ignore[arg-type]
        return Repository(
            id=r["id"],
            user_id=r.get("user_id", ""),
            name=r["name"],
            url=r.get("url"),
            source=RepositorySource(r.get("source", "github")),
            default_branch=r.get("default_branch", "main"),
            primary_language=r.get("primary_language"),
            status=RepositoryStatus(r.get("status", "pending")),
            error_message=r.get("error_message"),
            file_count=r.get("file_count", 0),
            chunk_count=r.get("chunk_count", 0),
            embedding_count=r.get("embedding_count", 0),
            size_bytes=r.get("size_bytes", 0),
            metadata=r.get("metadata", {}),
            last_indexed_at=r.get("last_indexed_at"),
            created_at=r.get("created_at", datetime.now(UTC)),
            updated_at=r.get("updated_at", datetime.now(UTC)),
        )
