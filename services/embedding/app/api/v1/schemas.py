"""Request/Response Pydantic schemas for the Embedding Service API."""

from datetime import datetime
from uuid import UUID

from ages_common.models.base import AgesBaseModel
from app.domain.entities import RepositorySource, RepositoryStatus


# ── Request Schemas ──

class CreateRepositoryRequest(AgesBaseModel):
    """Request body for POST /api/v1/repositories."""
    name: str
    url: str | None = None
    source: RepositorySource = RepositorySource.GITHUB
    default_branch: str = "main"


class IndexRepositoryRequest(AgesBaseModel):
    """Request body for POST /api/v1/repositories/{id}/index."""
    force_reindex: bool = False


# ── Response Schemas ──

class RepositoryResponse(AgesBaseModel):
    """Response model for a repository."""
    id: UUID
    user_id: str
    name: str
    url: str | None = None
    source: RepositorySource
    default_branch: str
    primary_language: str | None = None
    status: RepositoryStatus
    error_message: str | None = None
    file_count: int
    chunk_count: int
    embedding_count: int
    last_indexed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RepositoryListResponse(AgesBaseModel):
    """Response model for listing repositories."""
    success: bool = True
    data: list[RepositoryResponse]
    total: int


class IndexJobResponse(AgesBaseModel):
    """Response model for an indexing job status."""
    id: UUID
    repository_id: UUID
    status: RepositoryStatus
    files_discovered: int
    files_parsed: int
    chunks_created: int
    chunks_embedded: int
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
