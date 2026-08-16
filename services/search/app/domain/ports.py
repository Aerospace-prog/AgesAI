"""Domain ports (interfaces) for the Search Service."""

from abc import ABC, abstractmethod

from app.domain.entities import SearchQuery, SearchResult


class VectorSearchPort(ABC):
    """Port for vector similarity search (implemented by Qdrant adapter)."""

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.35,
        repository_ids: list[str] | None = None,
        languages: list[str] | None = None,
        chunk_types: list[str] | None = None,
    ) -> list[SearchResult]:
        """Perform vector similarity search with optional filters.

        Args:
            query_vector: The embedding vector of the search query.
            limit: Maximum number of results.
            score_threshold: Minimum similarity score.
            repository_ids: Filter by repository IDs.
            languages: Filter by programming languages.
            chunk_types: Filter by chunk types (function, class, etc.).

        Returns:
            List of search results ordered by score (descending).
        """
        ...


class FullTextSearchPort(ABC):
    """Port for full-text search (implemented by PostgreSQL FTS adapter)."""

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        repository_ids: list[str] | None = None,
        languages: list[str] | None = None,
    ) -> list[SearchResult]:
        """Perform full-text keyword search.

        Args:
            query: The raw text search query.
            limit: Maximum number of results.
            repository_ids: Filter by repository IDs.
            languages: Filter by programming languages.

        Returns:
            List of search results ordered by relevance.
        """
        ...


class QueryEmbedderPort(ABC):
    """Port for embedding search queries (implemented by OpenAI adapter)."""

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generate an embedding vector for a search query.

        Args:
            query: The raw text search query.

        Returns:
            The embedding vector.
        """
        ...
