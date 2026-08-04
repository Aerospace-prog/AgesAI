"""Unit tests for domain entities."""

from uuid import UUID

from app.domain.entities import (
    ChunkType,
    CodeChunk,
    IndexJob,
    Repository,
    RepositorySource,
    RepositoryStatus,
)


def test_repository_defaults() -> None:
    """Verify Repository entity defaults."""
    repo = Repository(user_id="user1", name="test-repo")

    assert isinstance(repo.id, UUID)
    assert repo.user_id == "user1"
    assert repo.status == RepositoryStatus.PENDING
    assert repo.source == RepositorySource.GITHUB
    assert repo.default_branch == "main"
    assert repo.file_count == 0
    assert repo.chunk_count == 0


def test_repository_status_transitions() -> None:
    """Verify RepositoryStatus enum values."""
    assert RepositoryStatus.PENDING == "pending"
    assert RepositoryStatus.CLONING == "cloning"
    assert RepositoryStatus.PARSING == "parsing"
    assert RepositoryStatus.EMBEDDING == "embedding"
    assert RepositoryStatus.READY == "ready"
    assert RepositoryStatus.FAILED == "failed"


def test_chunk_type_enum() -> None:
    """Verify ChunkType enum values."""
    assert ChunkType.FUNCTION == "function"
    assert ChunkType.CLASS == "class"
    assert ChunkType.METHOD == "method"
    assert ChunkType.MODULE == "module"
    assert ChunkType.INTERFACE == "interface"
    assert ChunkType.STRUCT == "struct"


def test_index_job_defaults() -> None:
    """Verify IndexJob entity defaults."""
    from uuid import uuid4
    repo_id = uuid4()
    job = IndexJob(repository_id=repo_id)

    assert job.repository_id == repo_id
    assert job.status == RepositoryStatus.PENDING
    assert job.files_discovered == 0
    assert job.chunks_created == 0
    assert job.completed_at is None
