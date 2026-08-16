"""Shared test fixtures for RAG Service."""

import pytest
from app.domain.entities import Citation, Conversation, Message, MessageRole
from uuid import uuid4


@pytest.fixture
def sample_citations() -> list[Citation]:
    return [
        Citation(
            repository_id="repo1",
            file_path="auth.py",
            start_line=1,
            end_line=15,
            name="login",
            signature="def login():",
            snippet="def login(): pass",
            score=0.95,
        ),
        Citation(
            repository_id="repo1",
            file_path="user.py",
            start_line=20,
            end_line=40,
            name="User",
            signature="class User:",
            snippet="class User: pass",
            score=0.82,
        ),
    ]
