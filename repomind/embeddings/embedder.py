"""Generate vector embeddings for text chunks using sentence-transformers."""

import numpy as np
from sentence_transformers import SentenceTransformer

from repomind.chunking.chunker import TextChunk
from repomind.utils.config import get_settings

DEFAULT_MODEL = "all-MiniLM-L6-v2"


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class Embedder:
    """Wraps a sentence-transformers model for chunk and query embeddings."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model or DEFAULT_MODEL
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Load the model once and reuse it (expensive to reload)."""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
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
            vectors = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise EmbeddingError("Failed to generate embeddings.") from exc

        return np.asarray(vectors, dtype=np.float32)

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
