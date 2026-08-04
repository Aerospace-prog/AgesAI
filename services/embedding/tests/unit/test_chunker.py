"""Unit tests for the SemanticChunker."""

from uuid import uuid4

from app.domain.entities import ChunkType
from app.infrastructure.semantic_chunker import SemanticChunker


def test_chunk_basic_nodes(sample_ast_nodes: list[dict]) -> None:
    """Chunker should produce CodeChunk entities from AST nodes."""
    chunker = SemanticChunker(min_lines=2, max_lines=200)
    repo_id = uuid4()

    chunks = chunker.chunk(
        nodes=sample_ast_nodes,
        file_path="src/main.py",
        language="python",
        repository_id=repo_id,
    )

    assert len(chunks) == 2
    assert chunks[0].name == "process_data"
    assert chunks[0].chunk_type == ChunkType.FUNCTION
    assert chunks[0].language == "python"
    assert chunks[0].file_path == "src/main.py"
    assert chunks[0].repository_id == repo_id
    assert chunks[0].content_hash  # SHA-256 hash should be generated

    assert chunks[1].name == "DataProcessor"
    assert chunks[1].chunk_type == ChunkType.CLASS


def test_chunk_filters_small_nodes() -> None:
    """Chunker should skip nodes below min_lines threshold."""
    chunker = SemanticChunker(min_lines=5, max_lines=200)

    small_node = [{
        "type": "function",
        "name": "tiny",
        "content": "def tiny(): pass",
        "start_line": 1,
        "end_line": 1,
    }]

    chunks = chunker.chunk(
        nodes=small_node,
        file_path="test.py",
        language="python",
        repository_id=uuid4(),
    )
    assert len(chunks) == 0


def test_chunk_splits_large_nodes() -> None:
    """Chunker should split oversized nodes into sub-chunks."""
    chunker = SemanticChunker(min_lines=2, max_lines=5)

    large_content = "\n".join([f"    line_{i} = {i}" for i in range(20)])
    large_node = [{
        "type": "function",
        "name": "big_function",
        "content": f"def big_function():\n{large_content}",
        "start_line": 1,
        "end_line": 21,
        "signature": "def big_function():",
    }]

    chunks = chunker.chunk(
        nodes=large_node,
        file_path="test.py",
        language="python",
        repository_id=uuid4(),
    )

    # Should produce multiple sub-chunks
    assert len(chunks) > 1
    assert chunks[0].name == "big_function_part1"
    # Each sub-chunk should have unique content hashes
    hashes = {c.content_hash for c in chunks}
    assert len(hashes) == len(chunks)


def test_chunk_type_mapping() -> None:
    """Verify all known node types are mapped correctly."""
    chunker = SemanticChunker()

    mappings = {
        "function": ChunkType.FUNCTION,
        "function_definition": ChunkType.FUNCTION,
        "class": ChunkType.CLASS,
        "class_declaration": ChunkType.CLASS,
        "method": ChunkType.METHOD,
        "interface_declaration": ChunkType.INTERFACE,
        "struct_definition": ChunkType.STRUCT,
        "enum_definition": ChunkType.ENUM,
        "unknown_type": ChunkType.BLOCK,
    }

    for node_type, expected in mappings.items():
        result = chunker._map_chunk_type(node_type)
        assert result == expected, f"{node_type} should map to {expected}, got {result}"


def test_code_chunk_to_embedding_text() -> None:
    """Verify CodeChunk.to_embedding_text() produces proper context."""
    from app.domain.entities import CodeChunk
    chunk = CodeChunk(
        repository_id=uuid4(),
        file_path="main.py",
        language="python",
        chunk_type=ChunkType.METHOD,
        name="do_work",
        signature="def do_work(self, data: list) -> None:",
        content="def do_work(self, data: list) -> None:\n    for item in data:\n        process(item)",
        start_line=10,
        end_line=12,
        parent_name="Worker",
        content_hash="test123",
        line_count=3,
    )

    text = chunk.to_embedding_text()
    assert "Language: python" in text
    assert "Type: method" in text
    assert "Parent: Worker" in text
    assert "Name: do_work" in text
    assert "Signature:" in text
    assert "process(item)" in text


def test_code_chunk_to_qdrant_payload() -> None:
    """Verify CodeChunk.to_qdrant_payload() produces correct metadata."""
    from app.domain.entities import CodeChunk
    repo_id = uuid4()
    chunk = CodeChunk(
        repository_id=repo_id,
        file_path="src/app.ts",
        language="typescript",
        chunk_type=ChunkType.FUNCTION,
        name="fetchData",
        content="async function fetchData() { ... }",
        start_line=1,
        end_line=5,
        content_hash="hash123",
        line_count=5,
    )

    payload = chunk.to_qdrant_payload()
    assert payload["repository_id"] == str(repo_id)
    assert payload["language"] == "typescript"
    assert payload["chunk_type"] == "function"
    assert payload["name"] == "fetchData"
    assert payload["content_hash"] == "hash123"
