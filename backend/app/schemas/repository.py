"""Schemas for repository analysis, overview, and lifecycle management."""

from pydantic import BaseModel, Field, model_validator


class AnalyzeRequest(BaseModel):
    """Request payload to analyze a repository."""

    url: str = Field(default="", description="GitHub repository URL or owner/repo format")
    repo_url: str | None = Field(default=None, description="Alternative field for repository URL")

    @model_validator(mode="after")
    def populate_url(self) -> "AnalyzeRequest":
        target = self.url or self.repo_url or ""
        if target:
            self.url = target.strip()
        return self


class AnalyzeResponse(BaseModel):
    """Initial summary response after repository ingestion and indexing."""

    repo_id: str = Field(..., description="Unique slug identifier (e.g. owner-repo)")
    repo_name: str = Field(..., description="Full repository name (e.g. owner/repo)")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    clone_url: str = Field(..., description="Git clone URL")
    local_path: str = Field(..., description="Absolute local path to cloned repository")
    was_cloned: bool = Field(..., description="True if cloned, False if loaded from local cache")
    scanned_files_count: int = Field(..., description="Total candidate files scanned")
    parsed_files_count: int = Field(..., description="Total supported text files parsed")
    chunks_count: int = Field(..., description="Total text chunks created")
    vectors_indexed: int = Field(..., description="Total vectors indexed in FAISS")
    embedding_dim: int = Field(..., description="Embedding dimension")
    status: str = Field(default="ready", description="Analysis status")


class OverviewMetrics(BaseModel):
    """Metrics displayed on the Overview tab."""

    files_indexed: int = Field(..., description="Number of parsed code/text files")
    chunks_created: int = Field(..., description="Number of chunked text slices")
    dependencies_found: int = Field(..., description="Internal + external imports")
    classes_detected: int = Field(..., description="Heuristic count of classes")
    functions_detected: int = Field(..., description="Heuristic count of functions/defs")
    entry_points_count: int = Field(..., description="Number of detected entry points")
    vectors_indexed: int = Field(..., description="Number of indexed vectors")
    embedding_dim: int = Field(..., description="Embedding dimension")
    skipped_unsupported: int = Field(..., description="Files skipped due to unsupported extension")
    skipped_unreadable: int = Field(..., description="Files skipped due to read errors")


class ChunkPreview(BaseModel):
    """Preview of a sample indexed chunk."""

    file_path: str
    chunk_index: int
    char_count: int
    content: str


class OverviewResponse(BaseModel):
    """Full overview tab data."""

    repo_id: str
    repo_name: str
    owner: str
    repo: str
    local_path: str
    was_cloned: bool
    metrics: OverviewMetrics
    architecture_summary: str | None = None
    chunk_previews: list[ChunkPreview] = Field(default_factory=list)
    supported_extensions: list[str] = Field(default_factory=list)


class ClearRequest(BaseModel):
    """Request payload to clear repository session."""

    delete_disk_cache: bool = Field(default=False, description="Whether to also delete local clone on disk")


class ClearResponse(BaseModel):
    """Response after clearing repository session."""

    repo_id: str
    status: str = "cleared"
    deleted_from_disk: bool = False
