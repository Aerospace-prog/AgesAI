"""Domain service — orchestrates the code indexing pipeline.

The EmbeddingService is the core business logic. It coordinates:
  Clone → Discover → Parse → Chunk → Hash → Embed → Store → Notify

It depends only on ports (abstractions), never on concrete infrastructure.
"""

import hashlib
import logging
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from app.domain.entities import (
    CodeChunk,
    IndexedFile,
    IndexJob,
    Repository,
    RepositorySource,
    RepositoryStatus,
)
from app.domain.ports import EmbedderPort, EventPublisherPort, RepositoryPort, VectorStorePort

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Orchestrates the full code indexing pipeline.

    This is the domain service — it contains business logic and coordinates
    infrastructure adapters through ports.
    """

    def __init__(
        self,
        repository_port: RepositoryPort,
        vector_store_port: VectorStorePort,
        embedder_port: EmbedderPort,
        event_publisher_port: EventPublisherPort,
        git_cloner: object,  # GitCloner from infrastructure
        parser: object,  # TreeSitterParser from infrastructure
        chunker: object,  # SemanticChunker from infrastructure
        config: object,  # EmbeddingSettings
    ) -> None:
        self._repo_port = repository_port
        self._vector_port = vector_store_port
        self._embedder_port = embedder_port
        self._event_port = event_publisher_port
        self._git_cloner = git_cloner
        self._parser = parser
        self._chunker = chunker
        self._config = config

    async def create_repository(
        self,
        user_id: str,
        name: str,
        url: str | None = None,
        source: RepositorySource = RepositorySource.GITHUB,
    ) -> Repository:
        """Create a new repository record and return it."""
        repo = Repository(
            user_id=user_id,
            name=name,
            url=url,
            source=source,
        )
        return await self._repo_port.create(repo)

    async def get_repository(self, repository_id: UUID) -> Repository | None:
        """Get a repository by ID."""
        return await self._repo_port.get_by_id(repository_id)

    async def get_user_repositories(self, user_id: str) -> list[Repository]:
        """Get all repositories for a user."""
        return await self._repo_port.get_by_user_id(user_id)

    async def index_repository(self, repository_id: UUID) -> IndexJob:
        """Execute the full indexing pipeline for a repository.

        Pipeline: Clone → Discover → Parse → Chunk → Hash → Embed → Store → Notify

        This is designed to run as a background task.
        """
        job = IndexJob(repository_id=repository_id)
        clone_dir = None

        try:
            # 1. Update status to CLONING
            await self._repo_port.update_status(repository_id, RepositoryStatus.CLONING)
            repo = await self._repo_port.get_by_id(repository_id)
            if not repo:
                raise ValueError(f"Repository {repository_id} not found")

            # 2. Clone the repository
            logger.info("Cloning repository: %s", repo.url or repo.name)
            clone_dir = await self._git_cloner.clone(  # type: ignore[attr-defined]
                url=repo.url,
                branch=repo.default_branch,
            )

            # 3. Update status to PARSING
            await self._repo_port.update_status(repository_id, RepositoryStatus.PARSING)

            # 4. Discover source files
            source_files = self._discover_files(clone_dir)
            job.files_discovered = len(source_files)
            logger.info("Discovered %d source files", len(source_files))

            # 5. Parse and chunk each file
            all_chunks: list[CodeChunk] = []
            indexed_files: list[IndexedFile] = []

            for file_path in source_files:
                try:
                    relative_path = os.path.relpath(file_path, clone_dir)
                    content = Path(file_path).read_text(encoding="utf-8", errors="replace")
                    content_hash = hashlib.sha256(content.encode()).hexdigest()
                    language = self._detect_language(file_path)

                    # Parse with tree-sitter
                    ast_nodes = await self._parser.parse(content, language)  # type: ignore[attr-defined]

                    # Chunk into semantic units
                    chunks = self._chunker.chunk(  # type: ignore[attr-defined]
                        nodes=ast_nodes,
                        file_path=relative_path,
                        language=language,
                        repository_id=repository_id,
                    )

                    all_chunks.extend(chunks)
                    job.files_parsed += 1

                    indexed_files.append(IndexedFile(
                        repository_id=repository_id,
                        file_path=relative_path,
                        language=language,
                        content_hash=content_hash,
                        chunk_count=len(chunks),
                        line_count=content.count("\n") + 1,
                        size_bytes=len(content.encode()),
                    ))
                except Exception as e:
                    logger.warning("Failed to parse %s: %s", file_path, str(e))
                    continue

            job.chunks_created = len(all_chunks)
            logger.info("Created %d chunks from %d files", len(all_chunks), job.files_parsed)

            # 6. Save indexed file records
            if indexed_files:
                await self._repo_port.save_indexed_files(indexed_files)

            # 7. Update status to EMBEDDING
            await self._repo_port.update_status(repository_id, RepositoryStatus.EMBEDDING)

            # 8. Generate embeddings in batches
            await self._vector_port.ensure_collection()
            batch_size = self._config.embedding_batch_size  # type: ignore[attr-defined]

            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i : i + batch_size]
                texts = [chunk.to_embedding_text() for chunk in batch]

                vectors = await self._embedder_port.embed_batch(texts)
                await self._vector_port.upsert_chunks(batch, vectors)
                job.chunks_embedded += len(batch)

                logger.debug(
                    "Embedded batch %d/%d (%d chunks)",
                    (i // batch_size) + 1,
                    (len(all_chunks) + batch_size - 1) // batch_size,
                    len(batch),
                )

            # 9. Update repository stats and status
            await self._repo_port.update_stats(
                repository_id,
                file_count=job.files_parsed,
                chunk_count=job.chunks_created,
                embedding_count=job.chunks_embedded,
            )
            await self._repo_port.update_status(repository_id, RepositoryStatus.READY)

            # 10. Publish success event
            await self._event_port.publish_repository_indexed(repository_id, job.chunks_embedded)

            job.status = RepositoryStatus.READY
            job.completed_at = datetime.now(UTC)
            logger.info(
                "Repository indexed successfully: repo=%s files=%d chunks=%d",
                repository_id, job.files_parsed, job.chunks_embedded,
            )

        except Exception as e:
            logger.error("Indexing failed for %s: %s", repository_id, str(e), exc_info=True)
            job.status = RepositoryStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(UTC)

            await self._repo_port.update_status(repository_id, RepositoryStatus.FAILED, str(e))
            await self._event_port.publish_repository_failed(repository_id, str(e))

        finally:
            # Cleanup cloned directory
            if clone_dir and os.path.exists(clone_dir):
                shutil.rmtree(clone_dir, ignore_errors=True)

        return job

    async def delete_repository(self, repository_id: UUID) -> None:
        """Delete a repository and all associated data (files, vectors, DB records)."""
        await self._repo_port.update_status(repository_id, RepositoryStatus.DELETING)
        await self._vector_port.delete_by_repository(repository_id)
        await self._repo_port.delete(repository_id)
        logger.info("Repository deleted: %s", repository_id)

    def _discover_files(self, root_dir: str) -> list[str]:
        """Walk the file tree and return paths of indexable source files."""
        result = []
        excluded_dirs = set(self._config.excluded_dirs)  # type: ignore[attr-defined]
        excluded_exts = set(self._config.excluded_extensions)  # type: ignore[attr-defined]
        supported_exts = set(self._config.supported_extensions)  # type: ignore[attr-defined]
        max_size = self._config.max_file_size_bytes  # type: ignore[attr-defined]

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Prune excluded directories
            dirnames[:] = [d for d in dirnames if d not in excluded_dirs]

            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in excluded_exts:
                    continue
                if supported_exts and ext not in supported_exts:
                    continue

                full_path = os.path.join(dirpath, fname)
                try:
                    if os.path.getsize(full_path) > max_size:
                        continue
                except OSError:
                    continue

                result.append(full_path)

        return sorted(result)

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_to_lang: dict[str, str] = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".tsx": "tsx", ".jsx": "jsx", ".go": "go", ".rs": "rust",
            ".java": "java", ".kt": "kotlin", ".cpp": "cpp", ".c": "c",
            ".h": "c", ".hpp": "cpp", ".cs": "csharp", ".rb": "ruby",
            ".php": "php", ".swift": "swift", ".scala": "scala",
            ".r": "r", ".sql": "sql", ".sh": "bash", ".bash": "bash",
            ".zsh": "zsh", ".yaml": "yaml", ".yml": "yaml",
            ".toml": "toml", ".json": "json", ".md": "markdown",
            ".dockerfile": "dockerfile",
        }
        ext = os.path.splitext(file_path)[1].lower()
        return ext_to_lang.get(ext, "unknown")
