"""Schemas for repository architecture analysis and dependency graph."""

from pydantic import BaseModel, Field


class FileConnectionSchema(BaseModel):
    """Connection statistics for one file in the dependency network."""

    file_path: str
    inbound: int
    outbound: int
    total: int


class DependencyEdgeSchema(BaseModel):
    """Directed import edge between source and target file."""

    source: str
    target: str
    is_internal: bool = True


class ArchitectureResponse(BaseModel):
    """Complete architecture analysis report."""

    repo_id: str
    repo_name: str
    files_analyzed: int
    internal_dependencies: int
    external_imports: int
    entry_points: list[str] = Field(default_factory=list)
    top_connected: list[FileConnectionSchema] = Field(default_factory=list)
    dependencies: list[DependencyEdgeSchema] = Field(default_factory=list)
    dot_graph: str = Field(default="", description="Graphviz DOT representation")
    architecture_summary: str | None = Field(default=None, description="Groq AI architecture summary")
    raw_context_text: str = Field(default="", description="Fallback text summary of static analysis")
