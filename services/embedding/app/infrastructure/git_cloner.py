"""Git cloner — clones repositories into temporary directories."""

import asyncio
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


class GitCloner:
    """Clones Git repositories using subprocess for isolation.

    Uses --depth=1 --single-branch for minimal clone size.
    """

    def __init__(self, timeout: int = 120, clone_depth: int = 1) -> None:
        self._timeout = timeout
        self._clone_depth = clone_depth

    async def clone(self, url: str | None, branch: str = "main") -> str:
        """Clone a repository and return the path to the cloned directory.

        Args:
            url: The Git repository URL.
            branch: The branch to clone.

        Returns:
            Path to the temporary directory containing the cloned repo.

        Raises:
            ValueError: If URL is None.
            RuntimeError: If git clone fails.
        """
        if not url:
            raise ValueError("Repository URL is required for cloning")

        clone_dir = tempfile.mkdtemp(prefix="ages-ai-repo-")

        cmd = [
            "git", "clone",
            "--depth", str(self._clone_depth),
            "--single-branch",
            "--branch", branch,
            url,
            clone_dir,
        ]

        logger.info("Cloning %s (branch=%s) into %s", url, branch, clone_dir)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self._timeout
            )

            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"git clone failed (exit {proc.returncode}): {error_msg}")

            logger.info("Clone complete: %s", clone_dir)
            return clone_dir

        except asyncio.TimeoutError:
            raise RuntimeError(f"git clone timed out after {self._timeout}s")
