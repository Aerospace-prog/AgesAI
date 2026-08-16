"""Shared test fixtures for the Search Service."""

import pytest
from app.domain.entities import SearchQuery, SearchResult, SearchType


@pytest.fixture
def sample_search_results() -> list[SearchResult]:
    """Sample SearchResult entities."""
    return [
        SearchResult(
            chunk_id="c1",
            score=0.92,
            repository_id="repo1",
            file_path="src/auth.py",
            language="python",
            chunk_type="function",
            name="verify_jwt",
            signature="def verify_jwt(token: str) -> dict:",
            start_line=10,
            end_line=25,
            parent_name="",
            content_hash="h1",
            line_count=15,
        ),
        SearchResult(
            chunk_id="c2",
            score=0.85,
            repository_id="repo1",
            file_path="src/auth.py",
            language="python",
            chunk_type="class",
            name="JWTVerifier",
            signature="class JWTVerifier:",
            start_line=30,
            end_line=60,
            parent_name="",
            content_hash="h2",
            line_count=30,
        ),
        SearchResult(
            chunk_id="c3",
            score=0.78,
            repository_id="repo1",
            file_path="src/db.py",
            language="python",
            chunk_type="function",
            name="connect_db",
            signature="async def connect_db() -> Pool:",
            start_line=1,
            end_line=12,
            parent_name="",
            content_hash="h3",
            line_count=12,
        ),
    ]
