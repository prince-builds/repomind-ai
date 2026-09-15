"""Schemas for interview pack generation."""

from pydantic import BaseModel, Field

from backend.app.schemas.common import RetrievalHitSchema


class InterviewRequest(BaseModel):
    """Interview generation prompt."""

    template: str = Field(default="System design interview questions (repo-wide)", description="Template name")
    prompt: str = Field(..., min_length=1, description="Interview generation prompt")
    top_k: int = Field(default=7, ge=1, le=20, description="Number of context chunks to retrieve")


class InterviewResponse(BaseModel):
    """Generated interview pack."""

    template: str
    prompt: str
    repo_name: str
    answer: str
    referenced_files: list[str] = Field(default_factory=list)
    retrieval_hits: list[RetrievalHitSchema] = Field(default_factory=list)
