"""Domain entities for the Search Service."""

from enum import StrEnum

from pydantic import Field

from ages_common.models.base import AgesBaseModel


class SearchType(StrEnum):
    """Type of search operation."""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchResult(AgesBaseModel):
    """A single search result from the vector store."""

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
    content_hash: str = ""
    line_count: int = 0
    snippet: str = ""  # Populated during result enrichment


class SearchResultGroup(AgesBaseModel):
    """Search results grouped by file path."""

    file_path: str
    language: str
    repository_id: str
    results: list[SearchResult] = Field(default_factory=list)
    total_score: float = 0.0

    @property
    def best_score(self) -> float:
        """Return the highest score in this group."""
        return max((r.score for r in self.results), default=0.0)


class SearchQuery(AgesBaseModel):
    """A user's search query with optional filters."""

    query: str
    repository_ids: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    chunk_types: list[str] = Field(default_factory=list)
    file_path_pattern: str | None = None
    limit: int = 10
    score_threshold: float = 0.35
    search_type: SearchType = SearchType.SEMANTIC


class SearchResponse(AgesBaseModel):
    """Complete search response with results and metadata."""

    query: str
    search_type: SearchType
    results: list[SearchResult] = Field(default_factory=list)
    grouped_results: list[SearchResultGroup] = Field(default_factory=list)
    total: int = 0
    search_time_ms: float = 0.0
