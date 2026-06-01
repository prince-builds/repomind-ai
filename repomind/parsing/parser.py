"""Read and parse repository text files into structured objects."""

from dataclasses import dataclass
from pathlib import Path

from repomind.parsing.supported_types import is_supported_file

# Read at most 2 MB per file to avoid loading huge assets into memory
MAX_FILE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class ParsedFile:
    """A successfully parsed source file."""

    repo_name: str
    file_path: str
    extension: str
    content: str
    line_count: int
    char_count: int


@dataclass(frozen=True)
class ParseSummary:
    """Results of parsing a batch of scanned files."""

    parsed_files: list[ParsedFile]
    skipped_unsupported: int
    skipped_unreadable: int


def read_text_file(file_path: Path) -> str | None:
    """
    Safely read a file as UTF-8 text.

    Returns None for binary, unreadable, or oversized files.
    """
    try:
        raw = file_path.read_bytes()
    except OSError:
        return None

    if len(raw) > MAX_FILE_BYTES:
        return None

    # Null bytes usually indicate binary content
    if b"\x00" in raw[:8192]:
        return None

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def parse_file(
    repo_root: Path,
    relative_path: Path,
    repo_name: str,
) -> ParsedFile | None:
    """
    Parse a single file if supported and readable.

    Returns None when the extension is unsupported or content cannot be read.
    """
    if not is_supported_file(relative_path):
        return None

    absolute = repo_root / relative_path
    content = read_text_file(absolute)
    if content is None:
        return None

    # Normalize path for metadata (always forward slashes)
    file_path = relative_path.as_posix()

    return ParsedFile(
        repo_name=repo_name,
        file_path=file_path,
        extension=relative_path.suffix.lower(),
        content=content,
        line_count=content.count("\n") + (1 if content and not content.endswith("\n") else 0),
        char_count=len(content),
    )


def parse_repository(
    repo_root: Path,
    relative_paths: list[Path],
    repo_name: str,
) -> ParseSummary:
    """
    Parse all scanned files under repo_root.

    Unsupported extensions and unreadable files are counted but skipped.
    """
    repo_root = Path(repo_root).resolve()
    parsed: list[ParsedFile] = []
    skipped_unsupported = 0
    skipped_unreadable = 0

    for rel in relative_paths:
        if not is_supported_file(rel):
            skipped_unsupported += 1
            continue

        result = parse_file(repo_root, rel, repo_name)
        if result is None:
            skipped_unreadable += 1
            continue

        parsed.append(result)

    return ParseSummary(
        parsed_files=parsed,
        skipped_unsupported=skipped_unsupported,
        skipped_unreadable=skipped_unreadable,
    )
