"""LiteLLM provider adapter implementing LLMProviderPort."""

import logging
from typing import AsyncGenerator
import litellm

from app.domain.ports import LLMProviderPort
from ages_common.exceptions import LLMError

logger = logging.getLogger(__name__)


class LiteLLMProvider(LLMProviderPort):
    """LiteLLM completion gateway providing model abstraction and streaming."""

    def __init__(self, openai_api_key: str = "", anthropic_api_key: str = "") -> None:
        if openai_api_key:
            litellm.openai_key = openai_api_key
        if anthropic_api_key:
            litellm.anthropic_key = anthropic_api_key
        litellm.drop_params = True

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream LLM completion tokens via LiteLLM."""
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content

        except Exception as e:
            logger.error("LiteLLM completion streaming failed for model %s: %s", model, str(e))
            raise LLMError(f"LiteLLM error: {e}")
