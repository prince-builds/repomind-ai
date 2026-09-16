"""Generate vector embeddings for text chunks using FastEmbed (ONNX Runtime)."""

import numpy as np
from fastembed import TextEmbedding

from repomind.chunking.chunker import TextChunk
from repomind.utils.config import get_settings

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _normalize_model_name(name: str) -> str:
    if name == "all-MiniLM-L6-v2":
        return "sentence-transformers/all-MiniLM-L6-v2"
    return name


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class Embedder:
    """Wraps a FastEmbed model for chunk and query embeddings."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        raw_name = model_name or settings.embedding_model or DEFAULT_MODEL
        self.model_name = _normalize_model_name(raw_name)
        self._model: TextEmbedding | None = None

    @property
    def model(self) -> TextEmbedding:
        """Load the model once and reuse it (threads=1 for memory efficiency)."""
        if self._model is None:
            try:
                self._model = TextEmbedding(
                    model_name=self.model_name,
                    threads=1,
                )
            except Exception as exc:
                raise EmbeddingError(
                    f"Failed to load embedding model '{self.model_name}'."
                ) from exc
        return self._model

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Embed a list of strings.

        Returns a float32 array of shape (n_texts, embedding_dim).
        """
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, 0)

        try:
            embeddings = list(self.model.embed(texts))
            return np.asarray(embeddings, dtype=np.float32)
        except Exception as exc:
            raise EmbeddingError("Failed to generate embeddings.") from exc

    def embed_chunks(self, chunks: list[TextChunk]) -> np.ndarray:
        """Embed chunk content while metadata stays on TextChunk objects."""
        texts = [chunk.content for chunk in chunks]
        return self.embed_texts(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single search query (shape: embedding_dim,)."""
        vectors = self.embed_texts([query.strip()])
        if vectors.size == 0:
            raise EmbeddingError("Query embedding is empty.")
        return vectors[0]

