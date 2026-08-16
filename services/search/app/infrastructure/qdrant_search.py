"""Qdrant vector search adapter — implements VectorSearchPort."""

import logging

from qdrant_client import models

from app.domain.entities import SearchResult
from app.domain.ports import VectorSearchPort
from ages_common.vector.qdrant import QdrantClient
from ages_common.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class QdrantSearchAdapter(VectorSearchPort):
    """Qdrant adapter for vector similarity search.

    Implements the VectorSearchPort interface.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str = "code_chunks",
    ) -> None:
        self._client = client
        self._collection_name = collection_name

    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.35,
        repository_ids: list[str] | None = None,
        languages: list[str] | None = None,
        chunk_types: list[str] | None = None,
    ) -> list[SearchResult]:
        """Perform filtered vector similarity search in Qdrant."""
        # Build Qdrant filter conditions
        must_conditions: list[models.Condition] = []

        if repository_ids:
            must_conditions.append(
                models.FieldCondition(
                    key="repository_id",
                    match=models.MatchAny(any=repository_ids),
                )
            )

        if languages:
            must_conditions.append(
                models.FieldCondition(
                    key="language",
                    match=models.MatchAny(any=languages),
                )
            )

        if chunk_types:
            must_conditions.append(
                models.FieldCondition(
                    key="chunk_type",
                    match=models.MatchAny(any=chunk_types),
                )
            )

        query_filter = models.Filter(must=must_conditions) if must_conditions else None

        try:
            scored_points = await self._client.search(
                collection_name=self._collection_name,
                vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                filter_conditions=query_filter,
            )

            results = []
            for point in scored_points:
                payload = point.payload or {}
                results.append(SearchResult(
                    chunk_id=str(point.id),
                    score=round(point.score, 4),
                    repository_id=payload.get("repository_id", ""),
                    file_path=payload.get("file_path", ""),
                    language=payload.get("language", ""),
                    chunk_type=payload.get("chunk_type", ""),
                    name=payload.get("name", ""),
                    signature=payload.get("signature", ""),
                    start_line=payload.get("start_line", 0),
                    end_line=payload.get("end_line", 0),
                    parent_name=payload.get("parent_name", ""),
                    content_hash=payload.get("content_hash", ""),
                    line_count=payload.get("line_count", 0),
                ))

            logger.debug(
                "Vector search: query_dim=%d limit=%d results=%d",
                len(query_vector), limit, len(results),
            )
            return results

        except Exception as e:
            logger.error("Vector search failed: %s", str(e))
            raise VectorStoreError(f"Vector search failed: {e}")
