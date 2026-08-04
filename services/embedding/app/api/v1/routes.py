"""API v1 routes for the Embedding Service."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ages_common.auth.dependencies import get_user_context
from ages_common.models.base import APIResponse, UserContext
from ages_common.exceptions import NotFoundError

from app.api.dependencies import get_embedding_service
from app.api.v1.schemas import (
    CreateRepositoryRequest,
    IndexJobResponse,
    RepositoryListResponse,
    RepositoryResponse,
)
from app.domain.services import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/", response_model=APIResponse, status_code=201)
async def create_repository(
    body: CreateRepositoryRequest,
    user: UserContext = Depends(get_user_context),
    service: EmbeddingService = Depends(get_embedding_service),
) -> APIResponse:
    """Create a new repository for indexing."""
    repo = await service.create_repository(
        user_id=user.user_id,
        name=body.name,
        url=body.url,
        source=body.source,
    )
    return APIResponse(
        data=RepositoryResponse.model_validate(repo.model_dump()),
        message=f"Repository '{body.name}' created successfully",
    )


@router.get("/", response_model=RepositoryListResponse)
async def list_repositories(
    user: UserContext = Depends(get_user_context),
    service: EmbeddingService = Depends(get_embedding_service),
) -> RepositoryListResponse:
    """List all repositories for the authenticated user."""
    repos = await service.get_user_repositories(user.user_id)
    return RepositoryListResponse(
        data=[RepositoryResponse.model_validate(r.model_dump()) for r in repos],
        total=len(repos),
    )


@router.get("/{repository_id}", response_model=APIResponse)
async def get_repository(
    repository_id: UUID,
    user: UserContext = Depends(get_user_context),
    service: EmbeddingService = Depends(get_embedding_service),
) -> APIResponse:
    """Get a repository by ID."""
    repo = await service.get_repository(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return APIResponse(
        data=RepositoryResponse.model_validate(repo.model_dump()),
    )


@router.post("/{repository_id}/index", response_model=APIResponse, status_code=202)
async def index_repository(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(get_user_context),
    service: EmbeddingService = Depends(get_embedding_service),
) -> APIResponse:
    """Start indexing a repository (runs as a background task).

    Returns 202 Accepted immediately. Use GET /repositories/{id} to check progress.
    """
    repo = await service.get_repository(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Queue the indexing as a background task
    background_tasks.add_task(service.index_repository, repository_id)

    return APIResponse(
        data={"repository_id": str(repository_id), "status": "indexing_queued"},
        message="Indexing started in background",
    )


@router.delete("/{repository_id}", response_model=APIResponse)
async def delete_repository(
    repository_id: UUID,
    user: UserContext = Depends(get_user_context),
    service: EmbeddingService = Depends(get_embedding_service),
) -> APIResponse:
    """Delete a repository and all its indexed data."""
    repo = await service.get_repository(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await service.delete_repository(repository_id)
    return APIResponse(
        message=f"Repository '{repo.name}' deleted successfully",
    )
