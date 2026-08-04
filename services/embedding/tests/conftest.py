"""Shared test fixtures for the Embedding Service."""

import pytest

from app.domain.entities import (
    ChunkType,
    CodeChunk,
    IndexJob,
    Repository,
    RepositorySource,
    RepositoryStatus,
)
from uuid import uuid4


@pytest.fixture
def sample_repository() -> Repository:
    """Create a sample Repository entity for testing."""
    return Repository(
        user_id="user_test_123",
        name="test-repo",
        url="https://github.com/test/test-repo.git",
        source=RepositorySource.GITHUB,
        default_branch="main",
    )


@pytest.fixture
def sample_chunks() -> list[CodeChunk]:
    """Create sample CodeChunk entities for testing."""
    repo_id = uuid4()
    return [
        CodeChunk(
            repository_id=repo_id,
            file_path="src/main.py",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            name="process_data",
            signature="def process_data(input: str) -> dict:",
            content='def process_data(input: str) -> dict:\n    """Process input data."""\n    return {"result": input}',
            start_line=1,
            end_line=3,
            parent_name=None,
            content_hash="abc123",
            line_count=3,
        ),
        CodeChunk(
            repository_id=repo_id,
            file_path="src/main.py",
            language="python",
            chunk_type=ChunkType.CLASS,
            name="DataProcessor",
            signature="class DataProcessor:",
            content='class DataProcessor:\n    """Processes data."""\n\n    def __init__(self):\n        self.data = []\n\n    def run(self):\n        pass',
            start_line=5,
            end_line=12,
            parent_name=None,
            content_hash="def456",
            line_count=8,
        ),
    ]


@pytest.fixture
def sample_ast_nodes() -> list[dict]:
    """Create sample AST nodes as the parser would produce."""
    return [
        {
            "type": "function",
            "name": "process_data",
            "content": 'def process_data(input: str) -> dict:\n    """Process input data."""\n    return {"result": input}',
            "start_line": 1,
            "end_line": 3,
            "signature": "def process_data(input: str) -> dict:",
            "parent_name": None,
        },
        {
            "type": "class",
            "name": "DataProcessor",
            "content": 'class DataProcessor:\n    """Processes data."""\n\n    def __init__(self):\n        self.data = []\n\n    def run(self):\n        pass',
            "start_line": 5,
            "end_line": 12,
            "signature": "class DataProcessor:",
            "parent_name": None,
        },
    ]
