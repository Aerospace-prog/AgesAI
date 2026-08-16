"""Cross-encoder reranker adapter implementing CrossEncoderRerankerPort."""

import logging
from app.domain.entities import Citation
from app.domain.ports import CrossEncoderRerankerPort

logger = logging.getLogger(__name__)


class CrossEncoderReranker(CrossEncoderRerankerPort):
    """Reranks citations based on exact keyword alignment and score decay.

    Allows fast lightweight reranking without heavy GPU dependencies.
    """

    async def rerank(
        self,
        query: str,
        citations: list[Citation],
        top_n: int = 5,
    ) -> list[Citation]:
        """Score and select top_n citations."""
        if not citations:
            return []

        query_terms = set(query.lower().split())

        scored_citations: list[tuple[float, Citation]] = []
        for citation in citations:
            text_to_match = f"{citation.file_path} {citation.name} {citation.signature} {citation.snippet}".lower()
            term_matches = sum(1 for term in query_terms if term in text_to_match)
            match_score = (term_matches / len(query_terms)) if query_terms else 0.0

            # Composite rank score = 70% vector/RRF score + 30% keyword match
            final_score = round(0.7 * citation.score + 0.3 * match_score, 4)

            scored_citations.append(
                (
                    final_score,
                    Citation(
                        repository_id=citation.repository_id,
                        file_path=citation.file_path,
                        start_line=citation.start_line,
                        end_line=citation.end_line,
                        name=citation.name,
                        signature=citation.signature,
                        snippet=citation.snippet,
                        score=final_score,
                    ),
                )
            )

        scored_citations.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_citations[:top_n]]
