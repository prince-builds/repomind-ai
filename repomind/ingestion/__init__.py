"""Load repositories and discover source files."""

from repomind.ingestion.file_filter import should_include_file, should_skip_dir
from repomind.ingestion.file_scanner import scan_repository
from repomind.ingestion.github_loader import (
    CloneResult,
    GitHubRepoInfo,
    GitHubURLError,
    clone_github_repo,
    get_repos_dir,
    parse_github_url,
)

__all__ = [
    "CloneResult",
    "GitHubRepoInfo",
    "GitHubURLError",
    "clone_github_repo",
    "get_repos_dir",
    "parse_github_url",
    "scan_repository",
    "should_include_file",
    "should_skip_dir",
]
