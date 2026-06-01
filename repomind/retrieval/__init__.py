"""FAISS-backed similarity search over embeddings."""

from repomind.retrieval.retriever import RetrievalHit, Retriever
from repomind.retrieval.vector_store import StoredChunk, VectorStore, VectorStoreError

__all__ = [
    "RetrievalHit",
    "Retriever",
    "StoredChunk",
    "VectorStore",
    "VectorStoreError",
]
