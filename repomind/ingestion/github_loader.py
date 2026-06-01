"""Clone GitHub repositories into local storage."""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from git import GitCommandError, Repo

from repomind.utils.config import get_settings

# owner/repo — allows dots and hyphens in names
_GITHUB_PATH_RE = re.compile(
    r"^/?(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


class GitHubURLError(ValueError):
    """Raised when a URL is not a valid GitHub repository URL."""


@dataclass(frozen=True)
class GitHubRepoInfo:
    """Parsed GitHub repository metadata."""

    owner: str
    repo: str
    full_name: str
    clone_url: str
    folder_name: str


@dataclass(frozen=True)
class CloneResult:
    """Outcome of a clone (or reuse) operation."""

    repo_info: GitHubRepoInfo
    local_path: Path
    was_cloned: bool


def get_repos_dir() -> Path:
    """Directory where cloned repositories are stored."""
    settings = get_settings()
    repos_dir = settings.data_dir / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)
    return repos_dir


def parse_github_url(url: str) -> GitHubRepoInfo:
    """
    Validate and parse a GitHub repository URL.

    Accepts:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      http://github.com/owner/repo/
    """
    raw = url.strip()
    if not raw:
        raise GitHubURLError("URL is empty.")

    # Allow bare owner/repo for convenience
    if "github.com" not in raw.lower() and "/" in raw and not raw.startswith("http"):
        raw = f"https://github.com/{raw.lstrip('/')}"

    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower().replace("www.", "")

    if host != "github.com":
        raise GitHubURLError(
            "Only github.com repository URLs are supported "
            f"(got host: {host or 'missing'})."
        )

    match = _GITHUB_PATH_RE.match(parsed.path or "")
    if not match:
        raise GitHubURLError(
            "Invalid GitHub URL. Use: https://github.com/owner/repository"
        )

    owner = match.group("owner")
    repo = match.group("repo")
    full_name = f"{owner}/{repo}"
    clone_url = f"https://github.com/{full_name}.git"
    folder_name = f"{owner}-{repo}"

    return GitHubRepoInfo(
        owner=owner,
        repo=repo,
        full_name=full_name,
        clone_url=clone_url,
        folder_name=folder_name,
    )


def _authenticated_clone_url(clone_url: str, token: str) -> str:
    """Inject a GitHub token into HTTPS clone URLs (optional, for private repos)."""
    if not token:
        return clone_url
    return clone_url.replace("https://", f"https://{token}@")


def clone_github_repo(url: str) -> CloneResult:
    """
    Clone a GitHub repository into repomind/data/repos/{owner}-{repo}/.

    If the repo is already cloned (.git present), reuses the local copy
    and does not clone again.
    """
    repo_info = parse_github_url(url)
    target_dir = get_repos_dir() / repo_info.folder_name

    if (target_dir / ".git").is_dir():
        return CloneResult(
            repo_info=repo_info,
            local_path=target_dir.resolve(),
            was_cloned=False,
        )

    if target_dir.exists() and any(target_dir.iterdir()):
        raise GitHubURLError(
            f"Target path exists but is not a git repo: {target_dir}. "
            "Remove it manually or choose a different repository."
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    clone_url = _authenticated_clone_url(repo_info.clone_url, settings.github_token)

    try:
        Repo.clone_from(clone_url, str(target_dir))
    except GitCommandError as exc:
        raise GitHubURLError(
            f"Failed to clone {repo_info.full_name}. "
            "Check the URL, network, and GITHUB_TOKEN for private repos."
        ) from exc

    return CloneResult(
        repo_info=repo_info,
        local_path=target_dir.resolve(),
        was_cloned=True,
    )
