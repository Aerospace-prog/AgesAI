"""Domain entities for the Embedding Service.

These are pure data classes with no infrastructure dependencies,
representing the core business objects of the indexing pipeline.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from ages_common.models.base import AgesBaseModel


# ── Enums ──

class RepositoryStatus(StrEnum):
    """Repository indexing lifecycle status."""
    PENDING = "pending"
    CLONING = "cloning"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"
    DELETING = "deleting"


class RepositorySource(StrEnum):
    """How the repository was ingested."""
    GITHUB = "github"
    UPLOAD = "upload"
    LOCAL = "local"


class ChunkType(StrEnum):
    """The semantic type of a code chunk."""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    BLOCK = "block"


# ── Entities ──

class Repository(AgesBaseModel):
    """A code repository submitted for indexing."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    name: str
    url: str | None = None
    source: RepositorySource = RepositorySource.GITHUB
    default_branch: str = "main"
    primary_language: str | None = None
    status: RepositoryStatus = RepositoryStatus.PENDING
    error_message: str | None = None
    file_count: int = 0
    chunk_count: int = 0
    embedding_count: int = 0
    size_bytes: int = 0
    metadata: dict = Field(default_factory=dict)
    last_indexed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IndexedFile(AgesBaseModel):
    """A file that has been parsed and indexed from a repository."""

    id: UUID = Field(default_factory=uuid4)
    repository_id: UUID
    file_path: str
    language: str | None = None
    content_hash: str  # SHA-256
    chunk_count: int = 0
    line_count: int = 0
    size_bytes: int = 0
    ast_metadata: dict = Field(default_factory=dict)
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CodeChunk(AgesBaseModel):
    """A semantic unit of code extracted by the parser/chunker.

    Each chunk becomes a vector in Qdrant with its metadata as payload.
    """

    id: UUID = Field(default_factory=uuid4)
    repository_id: UUID
    file_path: str
    language: str
    chunk_type: ChunkType
    name: str  # function/class/method name
    signature: str | None = None  # function signature line
    content: str  # the actual source code
    start_line: int
    end_line: int
    parent_name: str | None = None  # enclosing class/module name
    content_hash: str  # SHA-256 of content
    line_count: int = 0

    def to_embedding_text(self) -> str:
        """Format the chunk for embedding generation.

        Includes language, type, name, and signature as context
        before the code content for richer semantic embedding.
        """
        header_parts = [f"Language: {self.language}", f"Type: {self.chunk_type}"]
        if self.parent_name:
            header_parts.append(f"Parent: {self.parent_name}")
        header_parts.append(f"Name: {self.name}")
        if self.signature:
            header_parts.append(f"Signature: {self.signature}")
        header = "\n".join(header_parts)
        return f"{header}\n\n{self.content}"

    def to_qdrant_payload(self) -> dict:
        """Create the metadata payload stored alongside the vector in Qdrant."""
        return {
            "repository_id": str(self.repository_id),
            "file_path": self.file_path,
            "language": self.language,
            "chunk_type": self.chunk_type,
            "name": self.name,
            "signature": self.signature or "",
            "start_line": self.start_line,
            "end_line": self.end_line,
            "parent_name": self.parent_name or "",
            "content_hash": self.content_hash,
            "line_count": self.line_count,
        }


class IndexJob(AgesBaseModel):
    """Tracks the state of a repository indexing job."""

    id: UUID = Field(default_factory=uuid4)
    repository_id: UUID
    status: RepositoryStatus = RepositoryStatus.PENDING
    files_discovered: int = 0
    files_parsed: int = 0
    chunks_created: int = 0
    chunks_embedded: int = 0
    error_message: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
