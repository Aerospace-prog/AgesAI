"""Unit tests for RAGService pipeline and prompt assembly."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from uuid import uuid4

from app.domain.entities import ChatRequest, Citation, Conversation, Message, MessageRole
from app.domain.services import RAGService


@pytest.fixture
def mock_rag_service() -> RAGService:
    retriever = AsyncMock()
    reranker = AsyncMock()
    llm = AsyncMock()
    repo = AsyncMock()
    memory = AsyncMock()

    retriever.retrieve.return_value = [
        Citation(repository_id="r1", file_path="main.py", start_line=1, end_line=5, name="foo", snippet="foo code", score=0.9)
    ]
    reranker.rerank.return_value = [
        Citation(repository_id="r1", file_path="main.py", start_line=1, end_line=5, name="foo", snippet="foo code", score=0.95)
    ]

    async def mock_stream(*args, **kwargs):
        yield "Hello "
        yield "World"

    llm.stream_chat = mock_stream
    repo.get_conversation.return_value = None
    repo.create_conversation.return_value = Conversation(id=uuid4(), user_id="u1")
    memory.get_memory.return_value = []

    return RAGService(
        retriever=retriever,
        reranker=reranker,
        llm_provider=llm,
        conversation_repo=repo,
        memory=memory,
    )


@pytest.mark.asyncio
async def test_chat_stream_flow(mock_rag_service: RAGService) -> None:
    req = ChatRequest(message="How does foo work?")
    events = []
    async for event in mock_rag_service.chat_stream(req, user_id="u1"):
        events.append(event)

    assert len(events) >= 4
    assert "event: conversation_id" in events[0]
    assert "event: citations" in events[1]
    assert "event: delta" in events[2]
    assert "event: done" in events[-1]

    mock_rag_service._retriever.retrieve.assert_called_once()
    mock_rag_service._reranker.rerank.assert_called_once()
    mock_rag_service._repo.save_message.assert_called()
    mock_rag_service._memory.append_memory.assert_called_once()


def test_prompt_assembly(mock_rag_service: RAGService) -> None:
    citations = [
        Citation(repository_id="r1", file_path="auth.py", start_line=10, end_line=20, name="login", snippet="def login(): pass", score=0.9)
    ]
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]

    prompt = mock_rag_service._assemble_prompt(
        user_query="explain login",
        citations=citations,
        history=history,
    )

    assert len(prompt) == 4
    assert prompt[0]["role"] == "system"
    assert "RETRIEVED CODE CONTEXT" in prompt[0]["content"]
    assert "auth.py" in prompt[0]["content"]
    assert prompt[1]["role"] == "user"
    assert prompt[2]["role"] == "assistant"
    assert prompt[3]["content"] == "explain login"
