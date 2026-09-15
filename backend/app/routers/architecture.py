"""Architecture analysis and dependency network endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.architecture import (
    ArchitectureResponse,
    DependencyEdgeSchema,
    FileConnectionSchema,
)
from backend.app.store import repository_store

router = APIRouter(prefix="/api/repositories", tags=["Architecture"])


@router.get("/{repo_id}/architecture", response_model=ArchitectureResponse)
def get_repository_architecture(repo_id: str) -> ArchitectureResponse:
    """
    Retrieve dependency graph, top connected hub files, entry points, and AI summary.
    """
    session = repository_store.get(repo_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found. Analyze it first via POST /api/repositories/analyze.",
        )

    arch = session.architecture
    if not arch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Architecture report not available for repository '{repo_id}'.",
        )

    top_connected = [
        FileConnectionSchema(
            file_path=conn.file_path,
            inbound=conn.inbound,
            outbound=conn.outbound,
            total=conn.total,
        )
        for conn in arch.top_connected
    ]

    edges = arch.graph.internal_edges()
    dependencies = [
        DependencyEdgeSchema(
            source=edge.source,
            target=edge.target,
            is_internal=edge.is_internal,
        )
        for edge in edges[:100]  # Return up to 100 internal edges for visualization
    ]

    return ArchitectureResponse(
        repo_id=session.repo_id,
        repo_name=arch.repo_name,
        files_analyzed=arch.files_analyzed,
        internal_dependencies=arch.internal_dependencies,
        external_imports=arch.external_imports,
        entry_points=arch.entry_points,
        top_connected=top_connected,
        dependencies=dependencies,
        dot_graph=arch.graph.to_dot(max_edges=40),
        architecture_summary=session.architecture_summary,
        raw_context_text=arch.to_context_text(),
    )
