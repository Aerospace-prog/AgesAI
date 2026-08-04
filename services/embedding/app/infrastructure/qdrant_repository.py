"""Qdrant vector store adapter — implements VectorStorePort."""

import logging
from uuid import UUID

from qdrant_client import models

from app.domain.entities import CodeChunk
from app.domain.ports import VectorStorePort
from ages_common.vector.qdrant import QdrantClient
from ages_common.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class QdrantRepository(VectorStorePort):
    """Qdrant adapter for code chunk vector storage.

    Implements the VectorStorePort interface.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str = "code_chunks",
        vector_size: int = 1536,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._vector_size = vector_size

    async def ensure_collection(self) -> None:
        """Ensure the code_chunks collection exists with proper config."""
        await self._client.ensure_collection(
            collection_name=self._collection_name,
            vector_size=self._vector_size,
        )

        # Create payload indexes for filtered search
        try:
            await self._client.client.create_payload_index(
                collection_name=self._collection_name,
                field_name="repository_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            await self._client.client.create_payload_index(
                collection_name=self._collection_name,
                field_name="language",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            await self._client.client.create_payload_index(
                collection_name=self._collection_name,
                field_name="chunk_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            # Indexes may already exist
            pass

    async def upsert_chunks(self, chunks: list[CodeChunk], vectors: list[list[float]]) -> None:
        """Upsert code chunks with their embedding vectors."""
        ids = [str(chunk.id) for chunk in chunks]
        payloads = [chunk.to_qdrant_payload() for chunk in chunks]

        await self._client.upsert(
            collection_name=self._collection_name,
            ids=ids,
            vectors=vectors,
            payloads=payloads,
        )

    async def delete_by_repository(self, repository_id: UUID) -> None:
        """Delete all vectors belonging to a repository."""
        await self._client.delete_by_filter(
            collection_name=self._collection_name,
            filter_conditions=models.Filter(
                must=[
                    models.FieldCondition(
                        key="repository_id",
                        match=models.MatchValue(value=str(repository_id)),
                    )
                ]
            ),
        )
        logger.info("Deleted vectors for repository %s", repository_id)
