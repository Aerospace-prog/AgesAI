"""OpenAI query embedder adapter — implements QueryEmbedderPort."""

import logging

from openai import AsyncOpenAI

from app.domain.ports import QueryEmbedderPort
from ages_common.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class OpenAIQueryEmbedder(QueryEmbedderPort):
    """Embeds search queries using OpenAI's embedding API.

    Implements the QueryEmbedderPort interface.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions

    async def embed_query(self, query: str) -> list[float]:
        """Generate an embedding vector for a search query."""
        if not query.strip():
            raise EmbeddingError("Empty query cannot be embedded")

        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=[query],
                dimensions=self._dimensions,
            )
            vector = response.data[0].embedding
            logger.debug("Query embedded: %r (dim=%d)", query[:50], len(vector))
            return vector

        except Exception as e:
            logger.error("Query embedding failed: %s", str(e))
            raise EmbeddingError(f"Query embedding failed: {e}")
