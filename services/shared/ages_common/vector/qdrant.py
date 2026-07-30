"""Qdrant vector database client wrapper for AgesAI services.

Provides collection management, vector upsert, search, and health check
operations with typed payloads and structured logging.
"""

import logging
from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models

from ages_common.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class QdrantClient:
    """Async Qdrant client wrapper with collection management and search operations.

    Usage:
        qdrant = QdrantClient(url="http://localhost:6333")
        await qdrant.connect()

        await qdrant.ensure_collection("code_chunks", vector_size=1536)
        await qdrant.upsert("code_chunks", points=[...])
        results = await qdrant.search("code_chunks", vector=[...], limit=10)

        await qdrant.disconnect()
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: str | None = None,
        prefer_grpc: bool = True,
    ) -> None:
        self._url = url
        self._api_key = api_key
        self._prefer_grpc = prefer_grpc
        self._client: AsyncQdrantClient | None = None

    async def connect(self) -> None:
        """Initialize the Qdrant async client."""
        if self._client is not None:
            return

        self._client = AsyncQdrantClient(
            url=self._url,
            api_key=self._api_key,
            prefer_grpc=self._prefer_grpc,
        )
        logger.info("Qdrant client connected: %s", self._url)

    async def disconnect(self) -> None:
        """Close the Qdrant client."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Qdrant client disconnected")

    @property
    def client(self) -> AsyncQdrantClient:
        """Return the underlying client. Raises if not connected."""
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized — call connect() first")
        return self._client

    async def ensure_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,
        distance: models.Distance = models.Distance.COSINE,
        on_disk_payload: bool = True,
    ) -> None:
        """Create a collection if it does not already exist.

        Uses scalar quantization for memory efficiency (~4x reduction).
        """
        try:
            exists = await self.client.collection_exists(collection_name)
            if exists:
                logger.info("Collection '%s' already exists", collection_name)
                return

            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=distance,
                    on_disk=True,
                ),
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=20000,
                ),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        always_ram=True,
                    ),
                ),
                on_disk_payload=on_disk_payload,
            )
            logger.info(
                "Collection '%s' created (dim=%d, distance=%s, quantization=INT8)",
                collection_name, vector_size, distance.value,
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to ensure collection '{collection_name}': {e}")

    async def upsert(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        """Upsert vectors with payloads into a collection.

        Args:
            collection_name: Target collection.
            ids: Point IDs (UUIDs as strings).
            vectors: Embedding vectors.
            payloads: Metadata payloads for each vector.
        """
        if len(ids) != len(vectors) or len(ids) != len(payloads):
            raise ValueError("ids, vectors, and payloads must have the same length")

        try:
            points = [
                models.PointStruct(id=id_, vector=vec, payload=payload)
                for id_, vec, payload in zip(ids, vectors, payloads)
            ]
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            logger.debug("Upserted %d points to '%s'", len(points), collection_name)
        except Exception as e:
            raise VectorStoreError(f"Failed to upsert to '{collection_name}': {e}")

    async def search(
        self,
        collection_name: str,
        vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_conditions: models.Filter | None = None,
    ) -> list[models.ScoredPoint]:
        """Search for similar vectors in a collection.

        Args:
            collection_name: Target collection.
            vector: Query embedding vector.
            limit: Max number of results.
            score_threshold: Minimum score to include.
            filter_conditions: Optional Qdrant filter.

        Returns:
            List of scored points with payloads.
        """
        try:
            results = await self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions,
                with_payload=True,
            )
            return results.points
        except Exception as e:
            raise VectorStoreError(f"Search failed on '{collection_name}': {e}")

    async def delete_by_filter(
        self,
        collection_name: str,
        filter_conditions: models.Filter,
    ) -> None:
        """Delete points matching a filter condition."""
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(filter=filter_conditions),
            )
        except Exception as e:
            raise VectorStoreError(f"Delete failed on '{collection_name}': {e}")

    async def health_check(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False
