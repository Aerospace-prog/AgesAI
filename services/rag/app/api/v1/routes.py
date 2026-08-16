"""API v1 routes for RAG Service."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ages_common.auth.dependencies import get_user_context
from ages_common.models.base import APIResponse, UserContext

from app.api.dependencies import get_rag_service
from app.api.v1.schemas import (
    ChatRequestSchema,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from app.domain.entities import ChatRequest
from app.domain.services import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rag"])


@router.post("/chat")
async def chat_stream(
    body: ChatRequestSchema,
    user: UserContext = Depends(get_user_context),
    service: RAGService = Depends(get_rag_service),
) -> StreamingResponse:
    """Execute RAG pipeline and stream response tokens via Server-Sent Events (SSE)."""
    request = ChatRequest(
        message=body.message,
        conversation_id=body.conversation_id,
        repository_ids=body.repository_ids,
        model=body.model,
    )

    generator = service.chat_stream(request, user.user_id)
    return StreamingResponse(generator, media_type="text/event-stream")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    user: UserContext = Depends(get_user_context),
    service: RAGService = Depends(get_rag_service),
) -> ConversationListResponse:
    """List all conversations for authenticated user."""
    convs = await service._repo.list_conversations(user.user_id)
    return ConversationListResponse(
        data=[
            ConversationResponse(
                id=c.id,
                user_id=c.user_id,
                title=c.title,
                repository_ids=c.repository_ids,
                message_count=c.message_count,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in convs
        ],
        total=len(convs),
    )


@router.get("/conversations/{conversation_id}", response_model=APIResponse)
async def get_conversation(
    conversation_id: UUID,
    user: UserContext = Depends(get_user_context),
    service: RAGService = Depends(get_rag_service),
) -> APIResponse:
    """Get conversation metadata and message history."""
    conv = await service._repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await service._repo.get_recent_messages(conversation_id, limit=50)

    conv_data = ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        repository_ids=conv.repository_ids,
        message_count=conv.message_count,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    ).model_dump()

    msg_data = [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            citations=[c.model_dump() for c in m.citations],  # type: ignore[arg-type]
            model=m.model,
            created_at=m.created_at,
        ).model_dump()
        for m in reversed(messages)
    ]

    return APIResponse(data={"conversation": conv_data, "messages": msg_data})


@router.delete("/conversations/{conversation_id}", response_model=APIResponse)
async def delete_conversation(
    conversation_id: UUID,
    user: UserContext = Depends(get_user_context),
    service: RAGService = Depends(get_rag_service),
) -> APIResponse:
    """Delete a conversation thread."""
    conv = await service._repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await service._repo.delete_conversation(conversation_id)
    return APIResponse(message="Conversation deleted successfully")
