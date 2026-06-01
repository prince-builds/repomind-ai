"""In-memory FAISS vector index with chunk metadata."""

from dataclasses import dataclass

import faiss
import numpy as np

from repomind.chunking.chunker import TextChunk


@dataclass(frozen=True)
class StoredChunk:
    """Metadata stored beside each FAISS vector."""

    repo_name: str
    file_path: str
    chunk_index: int
    content: str


class VectorStoreError(Exception):
    """Raised when the vector store is used incorrectly."""


class VectorStore:
    """FAISS index with parallel metadata for each embedded chunk."""

    def __init__(self) -> None:
        self._index: faiss.Index | None = None
        self._metadata: list[StoredChunk] = []

    @property
    def size(self) -> int:
        return len(self._metadata)

    @property
    def is_built(self) -> bool:
        return self._index is not None and self.size > 0

    @property
    def embedding_dim(self) -> int:
        if self._index is None:
            return 0
        return int(self._index.d)

    def build(self, embeddings: np.ndarray, chunks: list[TextChunk]) -> None:
        """
        Build an in-memory FAISS index from embeddings and chunks.

        Vectors are L2-normalized; search uses inner product (cosine similarity).
        """
        if not chunks:
            raise VectorStoreError("Cannot build index with no chunks.")
        if embeddings.shape[0] != len(chunks):
            raise VectorStoreError(
                f"Embedding count ({embeddings.shape[0]}) "
                f"does not match chunk count ({len(chunks)})."
            )

        vectors = np.asarray(embeddings, dtype=np.float32)
        if vectors.ndim != 2:
            raise VectorStoreError("Embeddings must be a 2D array.")

        faiss.normalize_L2(vectors)
        dimension = vectors.shape[1]

        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)

        self._index = index
        self._metadata = [
            StoredChunk(
                repo_name=chunk.repo_name,
                file_path=chunk.file_path,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
            )
            for chunk in chunks
        ]

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> list[tuple[StoredChunk, float]]:
        """
        Find the most similar chunks to a query embedding.

        Returns (metadata, score) pairs sorted by score descending.
        """
        if not self.is_built or self._index is None:
            raise VectorStoreError("Index is not built. Call build() first.")

        k = min(top_k, self.size)
        if k <= 0:
            return []

        query = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query)

        scores, indices = self._index.search(query, k)
        results: list[tuple[StoredChunk, float]] = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append((self._metadata[int(idx)], float(score)))

        return results
