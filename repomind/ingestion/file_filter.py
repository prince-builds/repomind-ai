"""Rules for which files and folders enter the pipeline."""

from pathlib import Path

# Folder names to skip anywhere in the tree
SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    ".pytest_cache",
}

# Binary and media extensions (lowercase, with leading dot)
SKIP_EXTENSIONS = {
    # Python artifacts
    ".pyc",
    ".pyo",
    ".pyd",
    # Images
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".bmp",
    ".webp",
    ".svg",
    # Audio / video
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    # Archives and binaries
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".pdf",
    # Fonts
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
}


def should_skip_dir(dir_name: str) -> bool:
    """Return True if a directory should not be entered during scanning."""
    return dir_name in SKIP_DIRS


def should_include_file(relative_path: Path) -> bool:
    """Return True if this file should be indexed and explained."""
    if any(should_skip_dir(part) for part in relative_path.parts):
        return False

    suffix = relative_path.suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return False

    # Skip extensionless files that are often binary (e.g. LICENSE is text — keep those)
    # Hidden junk at repo root is still filtered by path rules above
    return True
