"""Gather indexed context and run per-file Groq analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repomind.architecture.dependency_graph import DependencyGraph
from repomind.architecture.dependency_resolver import DependencyResolver
from repomind.chunking.chunker import TextChunk
from repomind.explanations.repository_explainer import RepositoryExplainer
from repomind.llm.prompts import combine_rag_context
from repomind.parsing.parser import read_text_file
from repomind.retrieval.context_builder import (
    DEFAULT_MAX_CHARS_PER_FILE,
    ContextExpansionConfig,
    build_expanded_context,
)
from repomind.retrieval.retriever import RetrievalHit


def format_file_dependency_context(graph: DependencyGraph, file_path: str) -> str:
    """Summarize inbound/outbound edges for one file."""
    inbound = graph.inbound_sources(file_path)
    outbound = graph.outbound_targets(file_path)
    lines = [
        f"Selected file: {file_path}",
        "",
        "Imported by (inbound):",
    ]
    if inbound:
        lines.extend(f"  - {path}" for path in inbound)
    else:
        lines.append("  (none detected)")

    lines.append("")
    lines.append("Imports (outbound, internal):")
    if outbound:
        lines.extend(f"  - {path}" for path in outbound)
    else:
        lines.append("  (none detected)")

    return "\n".join(lines)


def gather_file_hits(
    chunks: list[TextChunk],
    repo_name: str,
    file_path: str,
    repo_root: Path,
) -> list[RetrievalHit]:
    """
    Return indexed chunks for a file, or a single synthetic hit from disk.

    Prefers chunked index content; falls back to reading the file from the clone.
    """
    file_chunks = sorted(
        (chunk for chunk in chunks if chunk.file_path == file_path),
        key=lambda chunk: chunk.chunk_index,
    )
    if file_chunks:
        return [
            RetrievalHit(
                repo_name=chunk.repo_name,
                file_path=chunk.file_path,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=1.0,
            )
            for chunk in file_chunks
        ]

    absolute = repo_root / Path(file_path)
    text = read_text_file(absolute)
    if not text:
        return []

    truncated = text[:DEFAULT_MAX_CHARS_PER_FILE]
    return [
        RetrievalHit(
            repo_name=repo_name,
            file_path=file_path,
            chunk_index=0,
            content=truncated,
            score=1.0,
        )
    ]


@dataclass(frozen=True)
class FileIntelligenceResult:
    """Structured output from per-file intelligence analysis."""

    file_path: str
    answer: str
    retrieval_hits: list[RetrievalHit]
    related_files: list[str]
    repo_name: str


def analyze_file(
    *,
    repo_name: str,
    repo_root: Path,
    file_path: str,
    chunks: list[TextChunk],
    graph: DependencyGraph | None,
    explainer: RepositoryExplainer | None = None,
) -> FileIntelligenceResult:
    """
    Build RAG context from indexed chunks, dependency graph, and neighbors; call Groq.
    """
    llm = explainer or RepositoryExplainer()
    hits = gather_file_hits(chunks, repo_name, file_path, repo_root)

    dependency_outline: str | None = None
    if graph is not None:
        dependency_outline = format_file_dependency_context(graph, file_path)

    neighbor_snippets = ()
    related_files: list[str] = []

    if hits and graph is not None:
        resolver = DependencyResolver(graph)
        expansion = build_expanded_context(
            repo_root,
            resolver,
            hits,
            ContextExpansionConfig(max_depth=1, max_related_files=8),
        )
        neighbor_snippets = expansion.neighbor_snippets
        related_files = list(expansion.related_files)

    context = combine_rag_context(hits, neighbor_snippets, dependency_outline)

    if not hits and not neighbor_snippets:
        context = (
            f"{context}\n\n"
            "(No indexed or readable content for this file. "
            "Analysis may be limited.)"
        )

    answer = llm.explain_file_intelligence(repo_name, file_path, context)

    return FileIntelligenceResult(
        file_path=file_path,
        answer=answer,
        retrieval_hits=hits,
        related_files=related_files,
        repo_name=repo_name,
    )
