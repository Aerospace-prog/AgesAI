"""Semantic chunker — splits parsed AST nodes into code chunks for embedding."""

import hashlib
import logging
from uuid import UUID

from app.domain.entities import ChunkType, CodeChunk

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Converts parsed AST nodes into CodeChunk entities.

    Each AST node (function, class, method, etc.) becomes one CodeChunk
    with metadata for the embedding pipeline.
    """

    def __init__(self, min_lines: int = 3, max_lines: int = 200) -> None:
        self._min_lines = min_lines
        self._max_lines = max_lines

    def chunk(
        self,
        nodes: list[dict],
        file_path: str,
        language: str,
        repository_id: UUID,
    ) -> list[CodeChunk]:
        """Convert AST nodes into CodeChunk entities.

        Args:
            nodes: List of parsed AST node dicts from the parser.
                   Each dict has: type, name, content, start_line, end_line,
                   signature (optional), parent_name (optional).
            file_path: Relative file path in the repository.
            language: Programming language.
            repository_id: Owning repository UUID.

        Returns:
            List of CodeChunk entities ready for embedding.
        """
        chunks: list[CodeChunk] = []

        for node in nodes:
            content = node.get("content", "")
            line_count = content.count("\n") + 1

            # Skip chunks that are too small or too large
            if line_count < self._min_lines:
                continue
            if line_count > self._max_lines:
                # Split oversized chunks into sub-chunks
                sub_chunks = self._split_large_chunk(node, file_path, language, repository_id)
                chunks.extend(sub_chunks)
                continue

            chunk_type = self._map_chunk_type(node.get("type", "block"))
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            chunk = CodeChunk(
                repository_id=repository_id,
                file_path=file_path,
                language=language,
                chunk_type=chunk_type,
                name=node.get("name", "anonymous"),
                signature=node.get("signature"),
                content=content,
                start_line=node.get("start_line", 0),
                end_line=node.get("end_line", 0),
                parent_name=node.get("parent_name"),
                content_hash=content_hash,
                line_count=line_count,
            )
            chunks.append(chunk)

        return chunks

    def _split_large_chunk(
        self,
        node: dict,
        file_path: str,
        language: str,
        repository_id: UUID,
    ) -> list[CodeChunk]:
        """Split an oversized node into multiple chunks."""
        content = node.get("content", "")
        lines = content.split("\n")
        chunks: list[CodeChunk] = []
        start_line = node.get("start_line", 0)

        for i in range(0, len(lines), self._max_lines):
            sub_lines = lines[i : i + self._max_lines]
            sub_content = "\n".join(sub_lines)
            if len(sub_lines) < self._min_lines:
                continue

            content_hash = hashlib.sha256(sub_content.encode("utf-8")).hexdigest()
            chunk = CodeChunk(
                repository_id=repository_id,
                file_path=file_path,
                language=language,
                chunk_type=self._map_chunk_type(node.get("type", "block")),
                name=f"{node.get('name', 'anonymous')}_part{i // self._max_lines + 1}",
                signature=node.get("signature") if i == 0 else None,
                content=sub_content,
                start_line=start_line + i,
                end_line=start_line + i + len(sub_lines) - 1,
                parent_name=node.get("parent_name"),
                content_hash=content_hash,
                line_count=len(sub_lines),
            )
            chunks.append(chunk)

        return chunks

    def _map_chunk_type(self, node_type: str) -> ChunkType:
        """Map parser node type strings to ChunkType enum."""
        mapping: dict[str, ChunkType] = {
            "function": ChunkType.FUNCTION,
            "function_definition": ChunkType.FUNCTION,
            "function_declaration": ChunkType.FUNCTION,
            "arrow_function": ChunkType.FUNCTION,
            "class": ChunkType.CLASS,
            "class_definition": ChunkType.CLASS,
            "class_declaration": ChunkType.CLASS,
            "method": ChunkType.METHOD,
            "method_definition": ChunkType.METHOD,
            "method_declaration": ChunkType.METHOD,
            "module": ChunkType.MODULE,
            "interface": ChunkType.INTERFACE,
            "interface_declaration": ChunkType.INTERFACE,
            "struct": ChunkType.STRUCT,
            "struct_definition": ChunkType.STRUCT,
            "enum": ChunkType.ENUM,
            "enum_definition": ChunkType.ENUM,
        }
        return mapping.get(node_type, ChunkType.BLOCK)
