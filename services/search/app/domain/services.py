"""Domain service — orchestrates search operations.

The SearchService coordinates:
  1. Query embedding
  2. Vector search (semantic)
  3. Full-text search (keyword)
  4. Reciprocal Rank Fusion (hybrid)
  5. Result grouping by file
  6. Snippet extraction
"""

import logging
import time
from collections import defaultdict

from app.domain.entities import (
    SearchQuery,
    SearchResponse,
    SearchResult,
    SearchResultGroup,
    SearchType,
)
from app.domain.ports import FullTextSearchPort, QueryEmbedderPort, VectorSearchPort

logger = logging.getLogger(__name__)


class SearchService:
    """Orchestrates semantic and hybrid search operations."""

    def __init__(
        self,
        vector_search: VectorSearchPort,
        full_text_search: FullTextSearchPort,
        query_embedder: QueryEmbedderPort,
        rrf_k: int = 60,
    ) -> None:
        self._vector_search = vector_search
        self._fts = full_text_search
        self._embedder = query_embedder
        self._rrf_k = rrf_k

    async def semantic_search(self, query: SearchQuery) -> SearchResponse:
        """Perform pure semantic (vector) search.

        Steps: Embed query → Vector search → Group → Return
        """
        start = time.monotonic()

        # 1. Embed the query
        query_vector = await self._embedder.embed_query(query.query)

        # 2. Vector search
        results = await self._vector_search.search(
            query_vector=query_vector,
            limit=query.limit,
            score_threshold=query.score_threshold,
            repository_ids=query.repository_ids or None,
            languages=query.languages or None,
            chunk_types=query.chunk_types or None,
        )

        # 3. Group results by file
        grouped = self._group_results(results)

        elapsed_ms = (time.monotonic() - start) * 1000

        logger.info(
            "Semantic search completed: query=%r results=%d time=%.1fms",
            query.query[:50], len(results), elapsed_ms,
        )

        return SearchResponse(
            query=query.query,
            search_type=SearchType.SEMANTIC,
            results=results,
            grouped_results=grouped,
            total=len(results),
            search_time_ms=round(elapsed_ms, 1),
        )

    async def hybrid_search(self, query: SearchQuery) -> SearchResponse:
        """Perform hybrid search (vector + full-text) with Reciprocal Rank Fusion.

        Steps: Embed query → Parallel vector + FTS → RRF fusion → Group → Return
        """
        start = time.monotonic()

        # 1. Embed the query
        query_vector = await self._embedder.embed_query(query.query)

        # 2. Parallel search (vector + full-text)
        vector_results = await self._vector_search.search(
            query_vector=query_vector,
            limit=query.limit * 2,  # Fetch more for fusion
            score_threshold=query.score_threshold * 0.8,  # Slightly lower threshold
            repository_ids=query.repository_ids or None,
            languages=query.languages or None,
            chunk_types=query.chunk_types or None,
        )

        fts_results = await self._fts.search(
            query=query.query,
            limit=query.limit,
            repository_ids=query.repository_ids or None,
            languages=query.languages or None,
        )

        # 3. Reciprocal Rank Fusion
        fused = self._reciprocal_rank_fusion(
            vector_results=vector_results,
            fts_results=fts_results,
            k=self._rrf_k,
            limit=query.limit,
        )

        # 4. Group results
        grouped = self._group_results(fused)

        elapsed_ms = (time.monotonic() - start) * 1000

        logger.info(
            "Hybrid search completed: query=%r vector=%d fts=%d fused=%d time=%.1fms",
            query.query[:50], len(vector_results), len(fts_results), len(fused), elapsed_ms,
        )

        return SearchResponse(
            query=query.query,
            search_type=SearchType.HYBRID,
            results=fused,
            grouped_results=grouped,
            total=len(fused),
            search_time_ms=round(elapsed_ms, 1),
        )

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[SearchResult],
        fts_results: list[SearchResult],
        k: int = 60,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Merge results from multiple retrievers using Reciprocal Rank Fusion (RRF).

        RRF score = Σ 1 / (k + rank_i) for each retriever

        This is a well-established technique for combining ranked lists
        without needing score normalization between different scoring systems.
        """
        rrf_scores: dict[str, float] = defaultdict(float)
        result_map: dict[str, SearchResult] = {}

        # Score from vector results
        for rank, result in enumerate(vector_results, start=1):
            key = f"{result.repository_id}:{result.file_path}:{result.start_line}"
            rrf_scores[key] += 1.0 / (k + rank)
            result_map[key] = result

        # Score from full-text results
        for rank, result in enumerate(fts_results, start=1):
            key = f"{result.repository_id}:{result.file_path}:{result.start_line}"
            rrf_scores[key] += 1.0 / (k + rank)
            if key not in result_map:
                result_map[key] = result

        # Sort by fused RRF score (descending)
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        # Build final result list with fused scores
        fused: list[SearchResult] = []
        for key in sorted_keys[:limit]:
            result = result_map[key]
            fused.append(SearchResult(
                chunk_id=result.chunk_id,
                score=round(rrf_scores[key], 6),
                repository_id=result.repository_id,
                file_path=result.file_path,
                language=result.language,
                chunk_type=result.chunk_type,
                name=result.name,
                signature=result.signature,
                start_line=result.start_line,
                end_line=result.end_line,
                parent_name=result.parent_name,
                content_hash=result.content_hash,
                line_count=result.line_count,
                snippet=result.snippet,
            ))

        return fused

    def _group_results(self, results: list[SearchResult]) -> list[SearchResultGroup]:
        """Group search results by file path for better UI presentation."""
        groups: dict[str, SearchResultGroup] = {}

        for result in results:
            key = f"{result.repository_id}:{result.file_path}"
            if key not in groups:
                groups[key] = SearchResultGroup(
                    file_path=result.file_path,
                    language=result.language,
                    repository_id=result.repository_id,
                )
            groups[key].results.append(result)
            groups[key].total_score += result.score

        # Sort groups by best score (descending)
        sorted_groups = sorted(groups.values(), key=lambda g: g.best_score, reverse=True)
        return sorted_groups
