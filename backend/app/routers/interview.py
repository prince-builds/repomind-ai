"""Interview pack and code review prompt generation endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.common import RetrievalHitSchema
from backend.app.schemas.interview import InterviewRequest, InterviewResponse
from backend.app.store import repository_store
from repomind.embeddings.embedder import EmbeddingError
from repomind.explanations.repository_explainer import RepositoryExplainer
from repomind.llm.explainer import LLMConfigError, LLMError
from repomind.retrieval.vector_store import VectorStoreError

router = APIRouter(prefix="/api/repositories", tags=["Interview"])


@router.post("/{repo_id}/interview", response_model=InterviewResponse)
def generate_interview_pack(repo_id: str, payload: InterviewRequest) -> InterviewResponse:
    """
    Generate an interview pack or code review prompts based on repository context.
    """
    session = repository_store.get(repo_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found. Analyze it first via POST /api/repositories/analyze.",
        )

    retriever = session.retriever
    if not retriever or not retriever.is_ready:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search index is not built for this repository. Cannot generate interview pack.",
        )

    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview prompt cannot be empty.",
        )

    repo_name = session.ingestion.clone.repo_info.full_name

    try:
        hits = retriever.query(prompt, top_k=payload.top_k)
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {exc}",
        ) from exc

    try:
        explainer = RepositoryExplainer()
        explanation = explainer.explain_user_question(repo_name, prompt, hits)
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
            detail=f"Interview generation failed: {exc}",
        ) from exc

    hits_schema = [
        RetrievalHitSchema(
            repo_name=hit.repo_name,
            file_path=hit.file_path,
            chunk_index=hit.chunk_index,
            content=hit.content,
            score=hit.score,
        )
        for hit in explanation.retrieval_hits
    ]

    return InterviewResponse(
        template=payload.template,
        prompt=prompt,
        repo_name=explanation.repo_name,
        answer=explanation.answer,
        referenced_files=explanation.referenced_files,
        retrieval_hits=hits_schema,
    )
