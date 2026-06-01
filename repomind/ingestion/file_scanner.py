"""Walk a repository and list candidate files."""

import os
from pathlib import Path

from repomind.ingestion.file_filter import should_include_file, should_skip_dir


def scan_repository(repo_root: Path) -> list[Path]:
    """
    Recursively scan repo_root and return relative paths of included files.

    Skips ignored directories during the walk (faster than blind rglob).
    """
    repo_root = Path(repo_root).resolve()
    if not repo_root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist: {repo_root}")

    files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Prune ignored folders so os.walk never enters them
        dirnames[:] = sorted(d for d in dirnames if not should_skip_dir(d))

        current = Path(dirpath)
        for filename in filenames:
            rel = (current / filename).relative_to(repo_root)
            if should_include_file(rel):
                files.append(rel)

    return sorted(files)
