"""File extensions supported by the text parser."""

from pathlib import Path

# Lowercase extensions including the dot
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".md",
        ".txt",
        ".json",
        ".html",
        ".css",
    }
)


def is_supported_file(relative_path: Path) -> bool:
    """Return True if this file extension can be parsed as text."""
    return relative_path.suffix.lower() in SUPPORTED_EXTENSIONS
