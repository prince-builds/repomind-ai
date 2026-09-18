"""Schemas for natural-language repository Q&A."""

from pydantic import BaseModel, Field

from backend.app.schemas.common import RetrievalHitSchema


class QARequest(BaseModel):
    """Natural-language question about the repository."""

    question: str = Field(..., min_length=1, description="Question to ask about the codebase")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of semantic chunks to retrieve")


class QAResponse(BaseModel):
    """Answer with source citations and retrieved context."""

    question: str
    repo_name: str
    answer: str
    referenced_files: list[str] = Field(default_factory=list)
    retrieval_hits: list[RetrievalHitSchema] = Field(default_factory=list)
