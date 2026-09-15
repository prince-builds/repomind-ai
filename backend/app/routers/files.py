"""File browsing, tree filtering, and File Intelligence endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.common import RetrievalHitSchema
from backend.app.schemas.files import (
    AnalyzeFileRequest,
    AnalyzeFileResponse,
    FileListResponse,
)
from backend.app.store import repository_store
from repomind.files.file_intelligence import analyze_file
from repomind.files.file_tree import build_file_tree, filter_paths
from repomind.llm.explainer import LLMConfigError, LLMError

router = APIRouter(prefix="/api/repositories", tags=["Files"])


@router.get("/{repo_id}/files", response_model=FileListResponse)
def get_repository_files(
    repo_id: str,
    query: str = Query(default="", description="Substring filter for paths"),
) -> FileListResponse:
    """
    Retrieve file tree hierarchy and paths with optional query substring filtering.
    """
    session = repository_store.get(repo_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found. Analyze it first via POST /api/repositories/analyze.",
        )

    all_paths = sorted(path.as_posix() for path in session.ingestion.files)
    filtered = filter_paths(all_paths, query)
    tree = build_file_tree(filtered)

    return FileListResponse(
        repo_id=session.repo_id,
        total_files=len(all_paths),
        filtered_count=len(filtered),
        paths=filtered,
        tree=tree,
    )


@router.post("/{repo_id}/files/analyze", response_model=AnalyzeFileResponse)
def analyze_repository_file(repo_id: str, payload: AnalyzeFileRequest) -> AnalyzeFileResponse:
    """
    Generate deep File Intelligence for a specific file using Groq AI + RAG + dependency graph.
    """
    session = repository_store.get(repo_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found. Analyze it first via POST /api/repositories/analyze.",
        )

    clean_file_path = payload.file_path.strip()
    all_paths = {path.as_posix() for path in session.ingestion.files}
    if clean_file_path not in all_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{clean_file_path}' does not exist in repository '{repo_id}'.",
        )

    repo_name = session.ingestion.clone.repo_info.full_name
    repo_root = session.ingestion.clone.local_path
    graph = session.architecture.graph if session.architecture else None

    try:
        result = analyze_file(
            repo_name=repo_name,
            repo_root=repo_root,
            file_path=clean_file_path,
            chunks=session.chunks,
            graph=graph,
        )
    except LLMConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Groq configuration error: {exc}",
        ) from exc
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Groq LLM error: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File analysis failed: {exc}",
        ) from exc

    hits_schema = [
        RetrievalHitSchema(
            repo_name=hit.repo_name,
            file_path=hit.file_path,
            chunk_index=hit.chunk_index,
            content=hit.content,
            score=hit.score,
        )
        for hit in result.retrieval_hits
    ]

    return AnalyzeFileResponse(
        file_path=result.file_path,
        repo_name=result.repo_name,
        answer=result.answer,
        related_files=result.related_files,
        retrieval_hits=hits_schema,
    )
