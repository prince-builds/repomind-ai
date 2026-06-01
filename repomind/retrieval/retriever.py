"""Semantic search over repository chunks."""

from dataclasses import dataclass

from repomind.chunking.chunker import TextChunk
from repomind.embeddings.embedder import Embedder, EmbeddingError
from repomind.retrieval.vector_store import VectorStore, VectorStoreError


@dataclass(frozen=True)
class RetrievalHit:
    """One chunk returned from a similarity search."""

    repo_name: str
    file_path: str
    chunk_index: int
    content: str
    score: float


class Retriever:
    """Embed chunks, index them in FAISS, and answer natural-language queries."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        default_top_k: int = 5,
    ) -> None:
        self.embedder = embedder or Embedder()
        self.store = VectorStore()
        self.default_top_k = default_top_k

    @property
    def is_ready(self) -> bool:
        return self.store.is_built

    def build_index(self, chunks: list[TextChunk]) -> None:
        """Embed all chunks and build the in-memory FAISS index."""
        if not chunks:
            raise VectorStoreError("No chunks available to index.")

        embeddings = self.embedder.embed_chunks(chunks)
        self.store.build(embeddings, chunks)

    def query(self, question: str, top_k: int | None = None) -> list[RetrievalHit]:
        """
        Search the index with a natural-language question.

        Returns ranked chunks with cosine similarity scores (higher = better).
        """
        if not self.is_ready:
            raise VectorStoreError("Retriever index is not built.")

        cleaned = question.strip()
        if not cleaned:
            return []

        k = top_k if top_k is not None else self.default_top_k

        try:
            query_vector = self.embedder.embed_query(cleaned)
            matches = self.store.search(query_vector, top_k=k)
        except (EmbeddingError, VectorStoreError):
            raise
        except Exception as exc:
            raise EmbeddingError("Search failed.") from exc

        return [
            RetrievalHit(
                repo_name=meta.repo_name,
                file_path=meta.file_path,
                chunk_index=meta.chunk_index,
                content=meta.content,
                score=score,
            )
            for meta, score in matches
        ]
