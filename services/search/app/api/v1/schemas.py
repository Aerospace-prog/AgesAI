"""Request/Response Pydantic schemas for the Search Service API."""

from ages_common.models.base import AgesBaseModel
from app.domain.entities import SearchResult, SearchResultGroup, SearchType


# ── Request Schemas ──

class SemanticSearchRequest(AgesBaseModel):
    """Request body for POST /api/v1/search."""
    query: str
    repository_ids: list[str] = []
    languages: list[str] = []
    chunk_types: list[str] = []
    limit: int = 10
    score_threshold: float = 0.35


class HybridSearchRequest(AgesBaseModel):
    """Request body for POST /api/v1/search/hybrid."""
    query: str
    repository_ids: list[str] = []
    languages: list[str] = []
    chunk_types: list[str] = []
    limit: int = 10
    score_threshold: float = 0.30


# ── Response Schemas ──

class SearchResultResponse(AgesBaseModel):
    """Individual search result in the response."""
    chunk_id: str
    score: float
    repository_id: str
    file_path: str
    language: str
    chunk_type: str
    name: str
    signature: str = ""
    start_line: int
    end_line: int
    parent_name: str = ""
    line_count: int = 0


class SearchResultGroupResponse(AgesBaseModel):
    """Search results grouped by file path."""
    file_path: str
    language: str
    repository_id: str
    results: list[SearchResultResponse]
    total_score: float


class SearchAPIResponse(AgesBaseModel):
    """Full search API response."""
    success: bool = True
    query: str
    search_type: str
    results: list[SearchResultResponse]
    grouped_results: list[SearchResultGroupResponse]
    total: int
    search_time_ms: float
