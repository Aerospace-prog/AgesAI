"""Domain ports (interfaces) for RAG Service."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from uuid import UUID

from app.domain.entities import Citation, Conversation, Message


class HybridRetrieverPort(ABC):
    """Port for retrieving relevant code chunks via vector + FTS hybrid search."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        repository_ids: list[str] | None = None,
        top_k: int = 20,
    ) -> list[Citation]:
        """Retrieve relevant code citations for context assembly."""
        ...


class CrossEncoderRerankerPort(ABC):
    """Port for reranking retrieved citations using relevance scoring."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        citations: list[Citation],
        top_n: int = 5,
    ) -> list[Citation]:
        """Rerank citations and select top_n most relevant ones."""
        ...


class LLMProviderPort(ABC):
    """Port for LLM completion and streaming (implemented via LiteLLM)."""

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream LLM completion tokens as an async generator."""
        ...


class ConversationRepositoryPort(ABC):
    """Port for persisting conversations and messages in PostgreSQL."""

    @abstractmethod
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        ...

    @abstractmethod
    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        ...

    @abstractmethod
    async def list_conversations(self, user_id: str) -> list[Conversation]:
        ...

    @abstractmethod
    async def delete_conversation(self, conversation_id: UUID) -> None:
        ...

    @abstractmethod
    async def save_message(self, message: Message) -> Message:
        ...

    @abstractmethod
    async def get_recent_messages(self, conversation_id: UUID, limit: int = 10) -> list[Message]:
        ...


class MemoryPort(ABC):
    """Port for short-term conversation memory (Redis cache)."""

    @abstractmethod
    async def get_memory(self, conversation_id: UUID) -> list[dict[str, str]]:
        ...

    @abstractmethod
    async def append_memory(self, conversation_id: UUID, user_msg: str, assistant_msg: str) -> None:
        ...
