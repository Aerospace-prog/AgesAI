"""PostgreSQL full-text search adapter — implements FullTextSearchPort."""

import logging

from app.domain.entities import SearchResult
from app.domain.ports import FullTextSearchPort
from ages_common.database.postgres import PostgresClient

logger = logging.getLogger(__name__)


class PostgresFullTextSearch(FullTextSearchPort):
    """PostgreSQL adapter for full-text keyword search using tsvector/tsquery.

    Implements the FullTextSearchPort interface.

    Searches across the indexed_files table joined with chunk metadata,
    using PostgreSQL's built-in full-text search capabilities with
    ts_rank for relevance scoring.
    """

    def __init__(self, client: PostgresClient) -> None:
        self._db = client

    async def search(
        self,
        query: str,
        limit: int = 10,
        repository_ids: list[str] | None = None,
        languages: list[str] | None = None,
    ) -> list[SearchResult]:
        """Perform full-text search across indexed code chunks.

        Uses plainto_tsquery for safe query parsing (handles operators in code queries).
        Falls back to an empty result set if no FTS table exists.
        """
        try:
            # Build dynamic WHERE clauses
            conditions = ["to_tsvector('english', c.name || ' ' || c.signature) @@ plainto_tsquery('english', $1)"]
            params: list[object] = [query]
            param_idx = 2

            if repository_ids:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(repository_ids)))
                conditions.append(f"c.repository_id::text IN ({placeholders})")
                params.extend(repository_ids)
                param_idx += len(repository_ids)

            if languages:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(languages)))
                conditions.append(f"c.language IN ({placeholders})")
                params.extend(languages)
                param_idx += len(languages)

            where_clause = " AND ".join(conditions)

            sql = f"""
                SELECT
                    c.id::text AS chunk_id,
                    ts_rank(to_tsvector('english', c.name || ' ' || c.signature),
                            plainto_tsquery('english', $1)) AS score,
                    c.repository_id::text,
                    c.file_path,
                    c.language,
                    c.chunk_type,
                    c.name,
                    COALESCE(c.signature, '') AS signature,
                    c.start_line,
                    c.end_line,
                    COALESCE(c.parent_name, '') AS parent_name,
                    COALESCE(c.content_hash, '') AS content_hash,
                    c.line_count
                FROM code_chunks c
                WHERE {where_clause}
                ORDER BY score DESC
                LIMIT ${param_idx}
            """
            params.append(limit)

            rows = await self._db.fetch(sql, *params)

            results = []
            for row in rows:
                r = dict(row)
                results.append(SearchResult(
                    chunk_id=r["chunk_id"],
                    score=round(float(r["score"]), 4),
                    repository_id=r["repository_id"],
                    file_path=r["file_path"],
                    language=r["language"],
                    chunk_type=r["chunk_type"],
                    name=r["name"],
                    signature=r["signature"],
                    start_line=r["start_line"],
                    end_line=r["end_line"],
                    parent_name=r["parent_name"],
                    content_hash=r["content_hash"],
                    line_count=r["line_count"],
                ))

            logger.debug("FTS search: query=%r results=%d", query[:50], len(results))
            return results

        except Exception as e:
            logger.warning("Full-text search failed (may need FTS table): %s", str(e))
            return []
