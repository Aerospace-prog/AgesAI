"""Domain entities for RAG Service."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from ages_common.models.base import AgesBaseModel


class MessageRole(StrEnum):
    """Role of a message sender in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Citation(AgesBaseModel):
    """Source code citation attached to an assistant response."""

    repository_id: str
    file_path: str
    start_line: int
    end_line: int
    name: str = ""
    signature: str = ""
    snippet: str = ""
    score: float = 0.0


class Message(AgesBaseModel):
    """A message within a conversation."""

    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: MessageRole
    content: str
    citations: list[Citation] = Field(default_factory=list)
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Conversation(AgesBaseModel):
    """A conversation thread containing multiple messages."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    title: str = "New Chat"
    repository_ids: list[str] = Field(default_factory=list)
    message_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatRequest(AgesBaseModel):
    """Request model for initiating/continuing a RAG chat."""

    message: str
    conversation_id: UUID | None = None
    repository_ids: list[str] = Field(default_factory=list)
    model: str | None = None
    stream: bool = True


class ChatStreamChunk(AgesBaseModel):
    """Individual chunk sent over SSE during streaming LLM output."""

    event: str  # "delta", "citations", "done", "error"
    data: str | dict
