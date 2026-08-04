"""OpenAI embedding adapter — implements EmbedderPort."""

import logging

from openai import AsyncOpenAI

from app.domain.ports import EmbedderPort
from ages_common.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class OpenAIEmbedder(EmbedderPort):
    """Generates embeddings using OpenAI's text-embedding API.

    Implements the EmbedderPort interface.
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

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (same order as input).

        Raises:
            EmbeddingError: If the API call fails.
        """
        if not texts:
            return []

        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions,
            )

            # Sort by index to guarantee order matches input
            embeddings = sorted(response.data, key=lambda x: x.index)
            vectors = [e.embedding for e in embeddings]

            logger.debug(
                "Embedded %d texts (model=%s, dims=%d)",
                len(texts), self._model, self._dimensions,
            )
            return vectors

        except Exception as e:
            logger.error("OpenAI embedding failed: %s", str(e))
            raise EmbeddingError(f"Embedding generation failed: {e}")
