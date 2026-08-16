"""Unit tests for search entities and models."""

from app.domain.entities import SearchQuery, SearchResult, SearchResultGroup, SearchType


def test_search_result_defaults() -> None:
    res = SearchResult(
        chunk_id="c1",
        score=0.9,
        repository_id="r1",
        file_path="main.py",
        language="python",
        chunk_type="function",
        name="foo",
        start_line=1,
        end_line=5,
    )
    assert res.score == 0.9
    assert res.signature == ""
    assert res.parent_name == ""


def test_search_result_grouping() -> None:
    r1 = SearchResult(
        chunk_id="c1", score=0.8, repository_id="r1", file_path="f1.py",
        language="python", chunk_type="func", name="f1", start_line=1, end_line=5,
    )
    r2 = SearchResult(
        chunk_id="c2", score=0.95, repository_id="r1", file_path="f1.py",
        language="python", chunk_type="class", name="C1", start_line=10, end_line=20,
    )
    group = SearchResultGroup(
        file_path="f1.py",
        language="python",
        repository_id="r1",
        results=[r1, r2],
        total_score=1.75,
    )

    assert group.best_score == 0.95
    assert len(group.results) == 2


def test_search_query_defaults() -> None:
    q = SearchQuery(query="authentication logic")
    assert q.limit == 10
    assert q.score_threshold == 0.35
    assert q.search_type == SearchType.SEMANTIC
    assert q.repository_ids == []
