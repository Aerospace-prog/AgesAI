"""Unit tests for RAG entities."""

from uuid import UUID
from app.domain.entities import Citation, Conversation, Message, MessageRole


def test_conversation_defaults() -> None:
    conv = Conversation(user_id="u123")
    assert isinstance(conv.id, UUID)
    assert conv.user_id == "u123"
    assert conv.title == "New Chat"
    assert conv.message_count == 0


def test_message_defaults() -> None:
    from uuid import uuid4
    cid = uuid4()
    msg = Message(conversation_id=cid, role=MessageRole.USER, content="Hello AI")
    assert msg.conversation_id == cid
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello AI"
    assert msg.citations == []
