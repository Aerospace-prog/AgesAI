"""Domain ports (interfaces) for the Embedding Service.

Ports define abstract contracts that infrastructure adapters implement.
This is the core of Clean Architecture — the domain layer depends on
abstractions, not concrete implementations.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import CodeChunk, IndexedFile, Repository, RepositoryStatus


class RepositoryPort(ABC):
    """Port for repository persistence operations (implemented by PostgreSQL adapter)."""

    @abstractmethod
    async def create(self, repository: Repository) -> Repository:
        """Persist a new repository record."""
        ...

    @abstractmethod
    async def get_by_id(self, repository_id: UUID) -> Repository | None:
        """Fetch a repository by its ID."""
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> list[Repository]:
        """Fetch all repositories owned by a user."""
        ...

    @abstractmethod
    async def update_status(
        self, repository_id: UUID, status: RepositoryStatus, error_message: str | None = None,
    ) -> None:
        """Update repository indexing status."""
        ...

    @abstractmethod
    async def update_stats(
        self, repository_id: UUID, file_count: int, chunk_count: int, embedding_count: int,
    ) -> None:
        """Update repository indexing statistics."""
        ...

    @abstractmethod
    async def delete(self, repository_id: UUID) -> None:
        """Delete a repository and its associated data."""
        ...

    @abstractmethod
    async def save_indexed_files(self, files: list[IndexedFile]) -> None:
        """Bulk save indexed file records."""
        ...


class VectorStorePort(ABC):
    """Port for vector storage operations (implemented by Qdrant adapter)."""

    @abstractmethod
    async def ensure_collection(self) -> None:
        """Ensure the vector collection exists with proper configuration."""
        ...

    @abstractmethod
    async def upsert_chunks(self, chunks: list[CodeChunk], vectors: list[list[float]]) -> None:
        """Upsert code chunk vectors with metadata payloads."""
        ...

    @abstractmethod
    async def delete_by_repository(self, repository_id: UUID) -> None:
        """Delete all vectors belonging to a repository."""
        ...


class EmbedderPort(ABC):
    """Port for embedding generation (implemented by OpenAI adapter)."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (same order as input texts).
        """
        ...


class EventPublisherPort(ABC):
    """Port for event publishing (implemented by Kafka adapter)."""

    @abstractmethod
    async def publish_repository_indexed(self, repository_id: UUID, chunk_count: int) -> None:
        """Publish a repository.indexed event."""
        ...

    @abstractmethod
    async def publish_repository_failed(self, repository_id: UUID, error: str) -> None:
        """Publish a repository.failed event."""
        ...
