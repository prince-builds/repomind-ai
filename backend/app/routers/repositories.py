"""Repository lifecycle and overview endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.repository import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChunkPreview,
    ClearRequest,
    ClearResponse,
    OverviewMetrics,
    OverviewResponse,
)
from backend.app.store import repository_store
from repomind.embeddings.embedder import EmbeddingError
from repomind.ingestion.github_loader import GitHubURLError
from repomind.parsing.supported_types import SUPPORTED_EXTENSIONS
from repomind.retrieval.vector_store import VectorStoreError

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_repository(payload: AnalyzeRequest) -> AnalyzeResponse:
    """
    Ingest, parse, chunk, embed, and analyze architecture for a GitHub repository.
    """
    if not payload.url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository URL cannot be empty.",
        )

    try:
        session = repository_store.analyze(payload.url.strip())
    except GitHubURLError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Index build error: {exc}",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        ) from exc

    info = session.ingestion.clone.repo_info
    vectors_count = session.retriever.store.size if session.retriever and session.retriever.is_ready else 0

    return AnalyzeResponse(
        repo_id=session.repo_id,
        repo_name=info.full_name,
        owner=info.owner,
        repo=info.repo,
        clone_url=info.clone_url,
        local_path=f"repomind/data/repos/{session.repo_id}",
        was_cloned=session.ingestion.clone.was_cloned,
        scanned_files_count=len(session.ingestion.files),
        parsed_files_count=len(session.parse_summary.parsed_files),
        chunks_count=len(session.chunks),
        vectors_indexed=vectors_count,
        embedding_dim=session.embedding_dim,
        status="ready",
    )


@router.get("/{repo_id}/overview", response_model=OverviewResponse)
def get_repository_overview(repo_id: str) -> OverviewResponse:
    """
    Retrieve repository overview metrics, chunk previews, and AI architecture summary.
    """
    session = repository_store.get(repo_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found. Analyze it first via POST /api/repositories/analyze.",
        )

    info = session.ingestion.clone.repo_info
    arch = session.architecture

    internal_deps = arch.internal_dependencies if arch else 0
    external_imports = arch.external_imports if arch else 0
    entry_points_count = len(arch.entry_points) if arch else 0
    vectors_count = session.retriever.store.size if session.retriever and session.retriever.is_ready else 0

    # Heuristic class and function counts from parsed files (same as Streamlit app)
    classes_detected = 0
    functions_detected = 0
    for parsed in session.parse_summary.parsed_files:
        text = parsed.content
        classes_detected += text.count("class ")
        functions_detected += text.count("def ") + text.count("function ")

    metrics = OverviewMetrics(
        files_indexed=len(session.parse_summary.parsed_files),
        chunks_created=len(session.chunks),
        dependencies_found=internal_deps + external_imports,
        classes_detected=classes_detected,
        functions_detected=functions_detected,
        entry_points_count=entry_points_count,
        vectors_indexed=vectors_count,
        embedding_dim=session.embedding_dim,
        skipped_unsupported=session.parse_summary.skipped_unsupported,
        skipped_unreadable=session.parse_summary.skipped_unreadable,
    )

    chunk_previews = [
        ChunkPreview(
            file_path=chunk.file_path,
            chunk_index=chunk.chunk_index,
            char_count=chunk.char_count,
            content=chunk.content[:400] + ("…" if len(chunk.content) > 400 else ""),
        )
        for chunk in session.chunks[:5]
    ]

    return OverviewResponse(
        repo_id=session.repo_id,
        repo_name=info.full_name,
        owner=info.owner,
        repo=info.repo,
        local_path=f"repomind/data/repos/{session.repo_id}",
        was_cloned=session.ingestion.clone.was_cloned,
        metrics=metrics,
        architecture_summary=session.architecture_summary,
        chunk_previews=chunk_previews,
        supported_extensions=sorted(SUPPORTED_EXTENSIONS),
    )


@router.post("/{repo_id}/clear", response_model=ClearResponse)
def clear_repository_session(repo_id: str, payload: ClearRequest | None = None) -> ClearResponse:
    """
    Clear repository session from memory and optionally delete disk cache.
    """
    delete_disk = payload.delete_disk_cache if payload else False
    cleared = repository_store.clear(repo_id, delete_disk=delete_disk)
    if not cleared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )
    return ClearResponse(
        repo_id=repo_id,
        status="cleared",
        deleted_from_disk=delete_disk,
    )
