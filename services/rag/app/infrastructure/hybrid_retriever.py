"""Hybrid retriever adapter implementing HybridRetrieverPort.

Executes parallel vector similarity search (Qdrant) and full-text search (PostgreSQL),
fusing results using Reciprocal Rank Fusion (RRF).
"""

import logging
from collections import defaultdict

from qdrant_client import models

from app.domain.entities import Citation
from app.domain.ports import HybridRetrieverPort
from ages_common.database.postgres import PostgresClient
from ages_common.vector.qdrant import QdrantClient
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class HybridRetrieverAdapter(HybridRetrieverPort):
    """Hybrid vector + FTS retriever with Reciprocal Rank Fusion."""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        postgres_client: PostgresClient,
        openai_key: str,
        collection_name: str = "code_chunks",
        embedding_model: str = "text-embedding-3-small",
        rrf_k: int = 60,
    ) -> None:
        self._qdrant = qdrant_client
        self._db = postgres_client
        self._openai = AsyncOpenAI(api_key=openai_key)
        self._collection = collection_name
        self._embedding_model = embedding_model
        self._rrf_k = rrf_k

    async def retrieve(
        self,
        query: str,
        repository_ids: list[str] | None = None,
        top_k: int = 20,
    ) -> list[Citation]:
        """Perform parallel vector + FTS search and fuse with RRF."""
        # 1. Embed query for vector search
        emb_res = await self._openai.embeddings.create(
            model=self._embedding_model,
            input=[query],
        )
        query_vector = emb_res.data[0].embedding

        # 2. Vector search via Qdrant
        vec_citations = await self._qdrant_search(query_vector, repository_ids, limit=top_k)

        # 3. FTS search via PostgreSQL
        fts_citations = await self._fts_search(query, repository_ids, limit=top_k)

        # 4. Reciprocal Rank Fusion
        fused = self._rrf_fuse(vec_citations, fts_citations, k=self._rrf_k, limit=top_k)
        return fused

    async def _qdrant_search(
        self, query_vector: list[float], repo_ids: list[str] | None, limit: int
    ) -> list[Citation]:
        must_cond = []
        if repo_ids:
            must_cond.append(
                models.FieldCondition(key="repository_id", match=models.MatchAny(any=repo_ids))
            )
        flt = models.Filter(must=must_cond) if must_cond else None

        points = await self._qdrant.search(
            collection_name=self._collection,
            vector=query_vector,
            limit=limit,
            score_threshold=0.25,
            filter_conditions=flt,
        )

        results = []
        for p in points:
            pl = p.payload or {}
            results.append(
                Citation(
                    repository_id=str(pl.get("repository_id", "")),
                    file_path=str(pl.get("file_path", "")),
                    start_line=int(pl.get("start_line", 0)),
                    end_line=int(pl.get("end_line", 0)),
                    name=str(pl.get("name", "")),
                    signature=str(pl.get("signature", "")),
                    snippet=str(pl.get("name", "")) + "\n" + str(pl.get("signature", "")),
                    score=float(p.score),
                )
            )
        return results

    async def _fts_search(self, query: str, repo_ids: list[str] | None, limit: int) -> list[Citation]:
        try:
            conds = ["to_tsvector('english', c.name || ' ' || c.signature) @@ plainto_tsquery('english', $1)"]
            params: list[object] = [query]
            idx = 2
            if repo_ids:
                ph = ", ".join(f"${idx + i}" for i in range(len(repo_ids)))
                conds.append(f"c.repository_id::text IN ({ph})")
                params.extend(repo_ids)
                idx += len(repo_ids)

            sql = f"""
                SELECT c.repository_id::text, c.file_path, c.start_line, c.end_line,
                       c.name, COALESCE(c.signature, '') as signature,
                       ts_rank(to_tsvector('english', c.name || ' ' || c.signature), plainto_tsquery('english', $1)) as score
                FROM code_chunks c
                WHERE {" AND ".join(conds)}
                ORDER BY score DESC LIMIT ${idx}
            """
            params.append(limit)

            rows = await self._db.fetch(sql, *params)
            results = []
            for r in rows:
                results.append(
                    Citation(
                        repository_id=r["repository_id"],
                        file_path=r["file_path"],
                        start_line=r["start_line"],
                        end_line=r["end_line"],
                        name=r["name"],
                        signature=r["signature"],
                        snippet=f"{r['name']}\n{r['signature']}",
                        score=float(r["score"]),
                    )
                )
            return results
        except Exception:
            return []

    def _rrf_fuse(
        self, vec_list: list[Citation], fts_list: list[Citation], k: int, limit: int
    ) -> list[Citation]:
        scores: dict[str, float] = defaultdict(float)
        cmap: dict[str, Citation] = {}

        for rank, c in enumerate(vec_list, start=1):
            key = f"{c.repository_id}:{c.file_path}:{c.start_line}"
            scores[key] += 1.0 / (k + rank)
            cmap[key] = c

        for rank, c in enumerate(fts_list, start=1):
            key = f"{c.repository_id}:{c.file_path}:{c.start_line}"
            scores[key] += 1.0 / (k + rank)
            if key not in cmap:
                cmap[key] = c

        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        fused = []
        for key in sorted_keys[:limit]:
            cit = cmap[key]
            fused.append(
                Citation(
                    repository_id=cit.repository_id,
                    file_path=cit.file_path,
                    start_line=cit.start_line,
                    end_line=cit.end_line,
                    name=cit.name,
                    signature=cit.signature,
                    snippet=cit.snippet,
                    score=round(scores[key], 6),
                )
            )
        return fused
