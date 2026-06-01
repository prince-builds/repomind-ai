"""Expand retrieval context by following internal dependency edges."""

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from repomind.architecture.dependency_resolver import DependencyResolver
from repomind.parsing.parser import read_text_file
from repomind.retrieval.retriever import RetrievalHit

# Avoid loading huge files into the LLM context
DEFAULT_MAX_CHARS_PER_FILE = 12_000


@dataclass(frozen=True)
class ContextExpansionConfig:
    """How far to walk the dependency graph when gathering neighbor files."""

    max_depth: int = 2
    max_related_files: int = 20
    max_chars_per_file: int = DEFAULT_MAX_CHARS_PER_FILE
    # Include files that import retrieved files (reverse direction)
    include_importers: bool = True


@dataclass(frozen=True)
class NeighborSnippet:
    """A related file included for extra context."""

    file_path: str
    depth: int
    content: str
    char_count: int


@dataclass(frozen=True)
class ExpandedRAGContext:
    """Primary retrieval hits plus dependency-expanded neighbor snippets."""

    primary_hits: list[RetrievalHit]
    related_files: tuple[str, ...]
    neighbor_snippets: tuple[NeighborSnippet, ...]
    traversal_depth_used: int

    @property
    def primary_file_paths(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(hit.file_path for hit in self.primary_hits))

    @property
    def expanded_char_count(self) -> int:
        """Total characters sent to the LLM (primary chunks + neighbor files)."""
        primary_chars = sum(len(hit.content) for hit in self.primary_hits)
        neighbor_chars = sum(n.char_count for n in self.neighbor_snippets)
        return primary_chars + neighbor_chars


class ContextBuilderError(Exception):
    """Raised when context expansion cannot read the repository."""


def _bfs_related_files(
    resolver: DependencyResolver,
    seed_files: set[str],
    config: ContextExpansionConfig,
) -> list[tuple[str, int]]:
    """
    Walk import edges up to max_depth and collect related file paths.

    Returns (file_path, depth) with depth measured from any seed file.
    Seeds are not included. No duplicate paths (first discovery wins = BFS min depth).
    """
    graph = resolver.graph
    visited: set[str] = set(seed_files)
    queue: deque[tuple[str, int]] = deque()

    for path in sorted(seed_files):
        queue.append((path, 0))

    results: list[tuple[str, int]] = []

    while queue and len(results) < config.max_related_files:
        current, depth = queue.popleft()
        if depth >= config.max_depth:
            continue

        next_depth = depth + 1
        neighbors: list[str] = []
        neighbors.extend(graph.outbound_targets(current))
        if config.include_importers:
            neighbors.extend(graph.inbound_sources(current))

        for neighbor in sorted(set(neighbors)):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            results.append((neighbor, next_depth))
            queue.append((neighbor, next_depth))
            if len(results) >= config.max_related_files:
                break

    results.sort(key=lambda item: (item[1], item[0]))
    return results


def build_expanded_context(
    repo_root: Path,
    resolver: DependencyResolver,
    primary_hits: list[RetrievalHit],
    config: ContextExpansionConfig | None = None,
) -> ExpandedRAGContext:
    """
    Gather neighbor file contents by following internal imports from retrieved files.

    Primary hits are unchanged; related snippets are appended for the LLM.
    """
    cfg = config or ContextExpansionConfig()
    repo_root = Path(repo_root).resolve()

    if not primary_hits:
        return ExpandedRAGContext(
            primary_hits=[],
            related_files=(),
            neighbor_snippets=(),
            traversal_depth_used=0,
        )

    seed_files = {hit.file_path for hit in primary_hits}
    related = _bfs_related_files(resolver, seed_files, cfg)

    snippets: list[NeighborSnippet] = []
    max_depth_seen = 0

    for file_path, depth in related:
        if file_path in seed_files:
            continue
        max_depth_seen = max(max_depth_seen, depth)
        absolute = repo_root / Path(file_path)
        try:
            text = read_text_file(absolute)
        except OSError as exc:
            raise ContextBuilderError(f"Cannot read file: {file_path}") from exc

        if text is None:
            continue

        truncated = text[: cfg.max_chars_per_file]
        snippets.append(
            NeighborSnippet(
                file_path=file_path,
                depth=depth,
                content=truncated,
                char_count=len(truncated),
            )
        )

    related_paths = tuple(snippet.file_path for snippet in snippets)

    return ExpandedRAGContext(
        primary_hits=list(primary_hits),
        related_files=related_paths,
        neighbor_snippets=tuple(snippets),
        traversal_depth_used=max_depth_seen,
    )
