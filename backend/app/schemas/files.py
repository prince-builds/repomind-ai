"""Schemas for repository file tree and file intelligence."""

from typing import Any
from pydantic import BaseModel, Field

from backend.app.schemas.common import RetrievalHitSchema


class FileListResponse(BaseModel):
    """File hierarchy and paths."""

    repo_id: str
    total_files: int
    filtered_count: int
    paths: list[str] = Field(default_factory=list)
    tree: dict[str, Any] = Field(default_factory=dict)


class AnalyzeFileRequest(BaseModel):
    """Request payload to analyze a specific file."""

    file_path: str = Field(..., description="Repository-relative file path (e.g. repomind/ui/app.py)")


class AnalyzeFileResponse(BaseModel):
    """Deep file intelligence analysis."""

    file_path: str
    repo_name: str
    answer: str = Field(..., description="Groq AI generated file explanation")
    related_files: list[str] = Field(default_factory=list)
    retrieval_hits: list[RetrievalHitSchema] = Field(default_factory=list)
