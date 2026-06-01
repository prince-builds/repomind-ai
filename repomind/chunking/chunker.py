"""Split parsed file content into overlapping text chunks."""

from dataclasses import dataclass

from repomind.parsing.parser import ParsedFile

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class TextChunk:
    """A slice of file content with retrieval metadata."""

    repo_name: str
    file_path: str
    chunk_index: int
    content: str
    char_count: int


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into fixed-size chunks with character overlap.

    Example: chunk_size=1000, overlap=150 → next chunk starts at char 850.
    """
    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        if end >= text_len:
            break
        start = end - overlap

    return chunks


def chunk_parsed_file(
    parsed: ParsedFile,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Turn one parsed file into a list of TextChunk objects."""
    pieces = split_text(parsed.content, chunk_size=chunk_size, overlap=overlap)
    return [
        TextChunk(
            repo_name=parsed.repo_name,
            file_path=parsed.file_path,
            chunk_index=index,
            content=piece,
            char_count=len(piece),
        )
        for index, piece in enumerate(pieces)
    ]


def chunk_parsed_files(
    parsed_files: list[ParsedFile],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Chunk every parsed file and return a flat list."""
    all_chunks: list[TextChunk] = []
    for parsed in parsed_files:
        all_chunks.extend(
            chunk_parsed_file(parsed, chunk_size=chunk_size, overlap=overlap)
        )
    return all_chunks
