"""In-memory repository state manager for active analysis sessions."""

from __future__ import annotations

import gc
import logging
import os
import resource
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from repomind.architecture.architecture_analyzer import (
    ArchitectureReport,
    analyze_repository as analyze_repo_arch,
    generate_architecture_summary,
)
from repomind.chunking.chunker import TextChunk, chunk_parsed_files
from repomind.embeddings.embedder import Embedder, EmbeddingError
from repomind.ingestion.file_scanner import scan_repository
from repomind.ingestion.github_loader import (
    CloneResult,
    GitHubURLError,
    clone_github_repo,
    parse_github_url,
)
from repomind.llm.explainer import LLMConfigError, LLMError
from repomind.parsing.parser import ParseSummary, parse_repository
from repomind.retrieval.retriever import Retriever

logger = logging.getLogger(__name__)


def get_current_rss_mb() -> float:
    """Return resident set size in megabytes for memory monitoring."""
    try:
        scale = 1024 * 1024 if sys.platform == "darwin" else 1024
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / scale
    except Exception:
        return 0.0


@dataclass(frozen=True)
class IngestionSummary:
    """Ingestion details."""

    clone: CloneResult
    files: list[Path]


@dataclass(frozen=True)
class RepositorySession:
    """Full analyzed repository state in memory."""

    repo_id: str
    ingestion: IngestionSummary
    parse_summary: ParseSummary
    chunks: list[TextChunk]
    retriever: Retriever | None
    embedding_dim: int
    architecture: ArchitectureReport | None
    architecture_summary: str | None


class RepositoryStore:
    """Manages active analyzed repository sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, RepositorySession] = {}
        self._embedder: Embedder | None = None

    def warmup(self) -> None:
        """Pre-load FastEmbed model on startup to prevent cold-start latency."""
        try:
            logger.info("Warming up FastEmbed embedding model...")
            self._embedder = Embedder()
            _ = self._embedder.model
            logger.info(f"FastEmbed model loaded successfully. Initial RSS: {get_current_rss_mb():.2f} MB")
        except Exception as exc:
            logger.warning(f"Could not pre-warm embedding model: {exc}")

    def analyze(self, repo_url: str) -> RepositorySession:
        """Run the full ingestion, parsing, chunking, embedding, and architecture pipeline with memory safeguards."""
        logger.info(f"[MEM 1/8] Before analysis ({repo_url}): RSS={get_current_rss_mb():.2f} MB")

        repo_info = parse_github_url(repo_url)
        repo_id = repo_info.folder_name

        # If already analyzed in memory, return cached session
        if repo_id in self._sessions:
            logger.info(f"Returning cached memory session for {repo_id}")
            return self._sessions[repo_id]

        clone_result = clone_github_repo(repo_url)
        repo_name = clone_result.repo_info.full_name
        local_path = clone_result.local_path
        logger.info(f"[MEM 2/8] After clone ({repo_name}): RSS={get_current_rss_mb():.2f} MB")

        scanned_files = scan_repository(local_path)
        max_files = int(os.getenv("MAX_REPO_FILES", "500"))
        if len(scanned_files) > max_files:
            raise ValueError(
                f"Repository contains {len(scanned_files)} files, which exceeds the limit of {max_files} files "
                "for the free tier sandbox. Please analyze a smaller repository or specific subfolder."
            )

        parse_summary = parse_repository(local_path, scanned_files, repo_name)
        gc.collect()
        logger.info(f"[MEM 3/8] After parse ({len(parse_summary.parsed_files)} files): RSS={get_current_rss_mb():.2f} MB")

        chunks = chunk_parsed_files(parse_summary.parsed_files)
        gc.collect()
        max_chunks = int(os.getenv("MAX_REPO_CHUNKS", "800"))
        if len(chunks) > max_chunks:
            raise ValueError(
                f"Repository generated {len(chunks)} text chunks, which exceeds the limit of {max_chunks} chunks "
                "for the free tier sandbox. Please analyze a smaller repository."
            )
        logger.info(f"[MEM 4/8] After chunk ({len(chunks)} chunks): RSS={get_current_rss_mb():.2f} MB")

        retriever: Retriever | None = None
        embedding_dim = 0

        if chunks:
            if self._embedder is None:
                self._embedder = Embedder()
            retriever = Retriever(embedder=self._embedder)
            retriever.build_index(chunks)
            embedding_dim = retriever.store.embedding_dim
            gc.collect()

        logger.info(f"[MEM 5/8] After embedding & FAISS index ({embedding_dim}d): RSS={get_current_rss_mb():.2f} MB")

        architecture = analyze_repo_arch(local_path, scanned_files, repo_name)
        logger.info(f"[MEM 6/8] After architecture AST graph: RSS={get_current_rss_mb():.2f} MB")

        architecture_summary: str | None = None
        try:
            architecture_summary = generate_architecture_summary(architecture)
        except (LLMConfigError, LLMError) as exc:
            logger.warning(f"LLM architecture summary skipped: {exc}")
            architecture_summary = None

        logger.info(f"[MEM 7/8] After architecture summary generation: RSS={get_current_rss_mb():.2f} MB")

        # Evict older sessions to stay strictly within 512 MB memory limit on Render Free
        max_cached_sessions = int(os.getenv("MAX_CACHED_SESSIONS", "1"))
        while len(self._sessions) >= max_cached_sessions:
            evicted_id = next(iter(self._sessions))
            logger.info(f"Evicting older cached session '{evicted_id}' to free RAM.")
            self._sessions.pop(evicted_id, None)
            gc.collect()

        ingestion = IngestionSummary(clone=clone_result, files=scanned_files)
        session = RepositorySession(
            repo_id=repo_id,
            ingestion=ingestion,
            parse_summary=parse_summary,
            chunks=chunks,
            retriever=retriever,
            embedding_dim=embedding_dim,
            architecture=architecture,
            architecture_summary=architecture_summary,
        )
        self._sessions[repo_id] = session
        gc.collect()

        logger.info(f"[MEM 8/8] Before returning response for {repo_id}: RSS={get_current_rss_mb():.2f} MB")
        return session

    def get(self, repo_id: str) -> RepositorySession | None:
        """Retrieve active repository session by repo_id."""
        return self._sessions.get(repo_id)

    def list_all(self) -> list[str]:
        """List all active repo_ids."""
        return list(self._sessions.keys())

    def clear(self, repo_id: str, delete_disk: bool = False) -> bool:
        """Evict session from memory and optionally remove cloned directory on disk."""
        session = self._sessions.pop(repo_id, None)
        gc.collect()
        if session is not None and delete_disk:
            local_path = session.ingestion.clone.local_path
            if local_path.exists() and local_path.is_dir():
                try:
                    shutil.rmtree(local_path)
                    logger.info(f"Deleted local clone at {local_path}")
                except Exception as exc:
                    logger.error(f"Failed to delete disk clone: {exc}")
            return True
        return session is not None


# Global singleton store instance
repository_store = RepositoryStore()
