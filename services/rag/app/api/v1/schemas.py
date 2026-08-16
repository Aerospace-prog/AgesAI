"""Request/Response Pydantic schemas for the RAG API."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ages_common.models.base import AgesBaseModel
from app.domain.entities import MessageRole


class ChatRequestSchema(AgesBaseModel):
    """Request schema for POST /api/v1/chat."""

    message: str
    conversation_id: UUID | None = None
    repository_ids: list[str] = Field(default_factory=list)
    model: str | None = None


class CitationSchema(AgesBaseModel):
    repository_id: str
    file_path: str
    start_line: int
    end_line: int
    name: str = ""
    signature: str = ""
    snippet: str = ""
    score: float = 0.0


class MessageResponse(AgesBaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    citations: list[CitationSchema] = Field(default_factory=list)
    model: str | None = None
    created_at: datetime


class ConversationResponse(AgesBaseModel):
    id: UUID
    user_id: str
    title: str
    repository_ids: list[str] = Field(default_factory=list)
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(AgesBaseModel):
    success: bool = True
    data: list[ConversationResponse]
    total: int
