"""Unit tests for domain services (EmbeddingService) with mocked ports."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domain.entities import Repository, RepositorySource, RepositoryStatus
from app.domain.services import EmbeddingService


@pytest.fixture
def mock_service() -> EmbeddingService:
    """Create an EmbeddingService with all ports mocked."""
    config = MagicMock()
    config.embedding_batch_size = 2
    config.excluded_dirs = [".git", "node_modules"]
    config.excluded_extensions = [".pyc"]
    config.supported_extensions = [".py", ".js"]
    config.max_file_size_bytes = 1_000_000

    return EmbeddingService(
        repository_port=AsyncMock(),
        vector_store_port=AsyncMock(),
        embedder_port=AsyncMock(),
        event_publisher_port=AsyncMock(),
        git_cloner=AsyncMock(),
        parser=AsyncMock(),
        chunker=MagicMock(),
        config=config,
    )


@pytest.mark.asyncio
async def test_create_repository(mock_service: EmbeddingService) -> None:
    """create_repository should persist via the repository port."""
    mock_service._repo_port.create.return_value = Repository(
        user_id="user1", name="test-repo", url="https://github.com/test/test.git",
    )

    repo = await mock_service.create_repository(
        user_id="user1",
        name="test-repo",
        url="https://github.com/test/test.git",
    )

    assert repo.name == "test-repo"
    assert repo.user_id == "user1"
    mock_service._repo_port.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_repositories(mock_service: EmbeddingService) -> None:
    """get_user_repositories should delegate to the repository port."""
    mock_service._repo_port.get_by_user_id.return_value = [
        Repository(user_id="user1", name="repo1"),
        Repository(user_id="user1", name="repo2"),
    ]

    repos = await mock_service.get_user_repositories("user1")

    assert len(repos) == 2
    mock_service._repo_port.get_by_user_id.assert_called_once_with("user1")


@pytest.mark.asyncio
async def test_delete_repository(mock_service: EmbeddingService) -> None:
    """delete_repository should clean up vectors and DB records."""
    repo_id = uuid4()

    await mock_service.delete_repository(repo_id)

    mock_service._repo_port.update_status.assert_called_with(
        repo_id, RepositoryStatus.DELETING
    )
    mock_service._vector_port.delete_by_repository.assert_called_with(repo_id)
    mock_service._repo_port.delete.assert_called_with(repo_id)


def test_discover_files(mock_service: EmbeddingService) -> None:
    """_discover_files should find supported files and skip excluded dirs/extensions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file structure
        os.makedirs(os.path.join(tmpdir, "src"))
        os.makedirs(os.path.join(tmpdir, "node_modules"))
        os.makedirs(os.path.join(tmpdir, ".git"))

        # Supported files
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(tmpdir, "src", "utils.js"), "w") as f:
            f.write("console.log('hello')")

        # Excluded files
        with open(os.path.join(tmpdir, "src", "compiled.pyc"), "w") as f:
            f.write("bytecode")
        with open(os.path.join(tmpdir, "node_modules", "dep.js"), "w") as f:
            f.write("dependency")
        with open(os.path.join(tmpdir, ".git", "config"), "w") as f:
            f.write("git config")

        # Unsupported extension
        with open(os.path.join(tmpdir, "src", "image.png"), "w") as f:
            f.write("not code")

        files = mock_service._discover_files(tmpdir)

        filenames = [os.path.basename(f) for f in files]
        assert "main.py" in filenames
        assert "utils.js" in filenames
        assert "compiled.pyc" not in filenames
        assert "dep.js" not in filenames
        assert "config" not in filenames
        assert "image.png" not in filenames


def test_detect_language(mock_service: EmbeddingService) -> None:
    """_detect_language should map extensions to language names."""
    cases = {
        "main.py": "python",
        "app.ts": "typescript",
        "index.tsx": "tsx",
        "handler.go": "go",
        "lib.rs": "rust",
        "Main.java": "java",
        "unknown.xyz": "unknown",
    }
    for filename, expected in cases.items():
        result = mock_service._detect_language(filename)
        assert result == expected, f"{filename} should detect as {expected}, got {result}"
