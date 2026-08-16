"""API v1 routes for the Search Service."""

import logging

from fastapi import APIRouter, Depends

from ages_common.auth.dependencies import get_user_context
from ages_common.models.base import UserContext

from app.api.dependencies import get_search_service
from app.api.v1.schemas import (
    HybridSearchRequest,
    SearchAPIResponse,
    SearchResultGroupResponse,
    SearchResultResponse,
    SemanticSearchRequest,
)
from app.domain.entities import SearchQuery, SearchType
from app.domain.services import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchAPIResponse)
async def semantic_search(
    body: SemanticSearchRequest,
    user: UserContext = Depends(get_user_context),
    service: SearchService = Depends(get_search_service),
) -> SearchAPIResponse:
    """Perform semantic (vector) code search.

    Embeds the query using the same model used for indexing,
    then performs cosine similarity search in Qdrant.
    """
    query = SearchQuery(
        query=body.query,
        repository_ids=body.repository_ids,
        languages=body.languages,
        chunk_types=body.chunk_types,
        limit=body.limit,
        score_threshold=body.score_threshold,
        search_type=SearchType.SEMANTIC,
    )

    response = await service.semantic_search(query)
    return _to_api_response(response)


@router.post("/hybrid", response_model=SearchAPIResponse)
async def hybrid_search(
    body: HybridSearchRequest,
    user: UserContext = Depends(get_user_context),
    service: SearchService = Depends(get_search_service),
) -> SearchAPIResponse:
    """Perform hybrid search (semantic + full-text) with Reciprocal Rank Fusion.

    Combines vector similarity search with PostgreSQL full-text search,
    using RRF to produce a single ranked result list.
    """
    query = SearchQuery(
        query=body.query,
        repository_ids=body.repository_ids,
        languages=body.languages,
        chunk_types=body.chunk_types,
        limit=body.limit,
        score_threshold=body.score_threshold,
        search_type=SearchType.HYBRID,
    )

    response = await service.hybrid_search(query)
    return _to_api_response(response)


def _to_api_response(response: object) -> SearchAPIResponse:
    """Convert domain SearchResponse to API response schema."""
    from app.domain.entities import SearchResponse
    r: SearchResponse = response  # type: ignore[assignment]
    return SearchAPIResponse(
        query=r.query,
        search_type=r.search_type,
        results=[
            SearchResultResponse(
                chunk_id=res.chunk_id,
                score=res.score,
                repository_id=res.repository_id,
                file_path=res.file_path,
                language=res.language,
                chunk_type=res.chunk_type,
                name=res.name,
                signature=res.signature,
                start_line=res.start_line,
                end_line=res.end_line,
                parent_name=res.parent_name,
                line_count=res.line_count,
            )
            for res in r.results
        ],
        grouped_results=[
            SearchResultGroupResponse(
                file_path=group.file_path,
                language=group.language,
                repository_id=group.repository_id,
                results=[
                    SearchResultResponse(
                        chunk_id=res.chunk_id,
                        score=res.score,
                        repository_id=res.repository_id,
                        file_path=res.file_path,
                        language=res.language,
                        chunk_type=res.chunk_type,
                        name=res.name,
                        signature=res.signature,
                        start_line=res.start_line,
                        end_line=res.end_line,
                        parent_name=res.parent_name,
                        line_count=res.line_count,
                    )
                    for res in group.results
                ],
                total_score=group.total_score,
            )
            for group in r.grouped_results
        ],
        total=r.total,
        search_time_ms=r.search_time_ms,
    )
