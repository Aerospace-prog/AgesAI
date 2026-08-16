"""Unit tests for SearchService logic (semantic search, hybrid RRF, grouping)."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from app.domain.entities import SearchQuery, SearchResult, SearchType
from app.domain.services import SearchService


@pytest.fixture
def mock_service() -> SearchService:
    vector_port = AsyncMock()
    fts_port = AsyncMock()
    embedder_port = AsyncMock()

    embedder_port.embed_query.return_value = [0.1] * 1536

    return SearchService(
        vector_search=vector_port,
        full_text_search=fts_port,
        query_embedder=embedder_port,
        rrf_k=60,
    )


@pytest.mark.asyncio
async def test_semantic_search(mock_service: SearchService, sample_search_results: list[SearchResult]) -> None:
    mock_service._vector_search.search.return_value = sample_search_results

    query = SearchQuery(query="verify jwt token", limit=5)
    resp = await mock_service.semantic_search(query)

    assert resp.query == "verify jwt token"
    assert resp.search_type == SearchType.SEMANTIC
    assert len(resp.results) == 3
    assert len(resp.grouped_results) == 2  # src/auth.py and src/db.py
    mock_service._embedder.embed_query.assert_called_once_with("verify jwt token")
    mock_service._vector_search.search.assert_called_once()


@pytest.mark.asyncio
async def test_hybrid_search_rrf(mock_service: SearchService) -> None:
    res_vec = [
        SearchResult(chunk_id="c1", score=0.9, repository_id="r1", file_path="auth.py", language="python", chunk_type="func", name="login", start_line=1, end_line=10),
        SearchResult(chunk_id="c2", score=0.8, repository_id="r1", file_path="user.py", language="python", chunk_type="func", name="get_user", start_line=1, end_line=10),
    ]
    res_fts = [
        SearchResult(chunk_id="c2", score=5.0, repository_id="r1", file_path="user.py", language="python", chunk_type="func", name="get_user", start_line=1, end_line=10),
        SearchResult(chunk_id="c3", score=3.0, repository_id="r1", file_path="config.py", language="python", chunk_type="func", name="load_auth", start_line=1, end_line=10),
    ]

    mock_service._vector_search.search.return_value = res_vec
    mock_service._fts.search.return_value = res_fts

    query = SearchQuery(query="auth user login", limit=10)
    resp = await mock_service.hybrid_search(query)

    assert resp.search_type == SearchType.HYBRID
    # c2 is in both vector and fts, so its RRF rank should boost it to top or near top
    assert len(resp.results) == 3
    chunk_ids = [r.chunk_id for r in resp.results]
    assert "c2" in chunk_ids
    assert "c1" in chunk_ids
    assert "c3" in chunk_ids
