"""In-memory repository state manager for active analysis sessions."""

from __future__ import annotations

import logging
import shutil
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
        """Pre-load SentenceTransformer model on startup to prevent cold-start latency."""
        try:
            logger.info("Warming up SentenceTransformer embedding model...")
            self._embedder = Embedder()
            _ = self._embedder.model
            logger.info("Embedding model loaded successfully.")
        except Exception as exc:
            logger.warning(f"Could not pre-warm embedding model: {exc}")

    def analyze(self, repo_url: str) -> RepositorySession:
        """Run the full ingestion, parsing, chunking, embedding, and architecture pipeline."""
        repo_info = parse_github_url(repo_url)
        repo_id = repo_info.folder_name

        # If already analyzed in memory, return cached session
        if repo_id in self._sessions:
            logger.info(f"Returning cached memory session for {repo_id}")
            return self._sessions[repo_id]

        clone_result = clone_github_repo(repo_url)
        repo_name = clone_result.repo_info.full_name
        local_path = clone_result.local_path

        scanned_files = scan_repository(local_path)
        parse_summary = parse_repository(local_path, scanned_files, repo_name)
        chunks = chunk_parsed_files(parse_summary.parsed_files)

        retriever: Retriever | None = None
        embedding_dim = 0

        if chunks:
            retriever = Retriever(embedder=self._embedder)
            retriever.build_index(chunks)
            embedding_dim = retriever.store.embedding_dim

        architecture = analyze_repo_arch(local_path, scanned_files, repo_name)
        architecture_summary: str | None = None
        try:
            architecture_summary = generate_architecture_summary(architecture)
        except (LLMConfigError, LLMError) as exc:
            logger.warning(f"LLM architecture summary skipped: {exc}")
            architecture_summary = None

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
