"""Common schemas shared across endpoints."""

from pydantic import BaseModel, Field


class RetrievalHitSchema(BaseModel):
    """A single retrieved chunk with metadata and score."""

    repo_name: str = Field(..., description="Repository full name, e.g. owner/repo")
    file_path: str = Field(..., description="Repository-relative file path")
    chunk_index: int = Field(..., description="Index of chunk within file")
    content: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Similarity score (cosine)")


class ErrorResponse(BaseModel):
    """Standard error response structure."""

    detail: str = Field(..., description="Error message description")
