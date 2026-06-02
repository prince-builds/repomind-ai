"""Generate repository explanations from retrieval results."""

from dataclasses import dataclass

from repomind.llm.explainer import LLMExplainer
from repomind.llm.prompts import (
    build_architecture_prompt,
    build_chunk_summary_prompt,
    build_code_purpose_prompt,
    build_file_intelligence_prompt,
    build_file_responsibilities_prompt,
    build_question_prompt,
    format_retrieved_context,
)
from repomind.retrieval.retriever import RetrievalHit


@dataclass(frozen=True)
class ExplanationResult:
    """Structured output from an LLM explanation."""

    answer: str
    referenced_files: list[str]
    retrieval_hits: list[RetrievalHit]
    repo_name: str
    question: str


class RepositoryExplainer:
    """
    Turn retrieved chunks into natural-language explanations.

    Retrieval stays outside this class — pass in hits from Retriever.query().
    """

    def __init__(self, llm: LLMExplainer | None = None) -> None:
        self.llm = llm or LLMExplainer()

    @staticmethod
    def referenced_files(hits: list[RetrievalHit]) -> list[str]:
        """Unique file paths from retrieval hits, sorted."""
        return sorted({hit.file_path for hit in hits})

    def explain_user_question(
        self,
        repo_name: str,
        question: str,
        hits: list[RetrievalHit],
    ) -> ExplanationResult:
        """Answer a user question using retrieved chunks as context."""
        context = format_retrieved_context(hits)
        prompt = build_question_prompt(repo_name, question, context)
        answer = self.llm.complete(prompt)

        return ExplanationResult(
            answer=answer,
            referenced_files=self.referenced_files(hits),
            retrieval_hits=hits,
            repo_name=repo_name,
            question=question,
        )

    def explain_architecture(
        self,
        repo_name: str,
        hits: list[RetrievalHit],
    ) -> ExplanationResult:
        context = format_retrieved_context(hits)
        prompt = build_architecture_prompt(repo_name, context)
        answer = self.llm.complete(prompt)
        return ExplanationResult(
            answer=answer,
            referenced_files=self.referenced_files(hits),
            retrieval_hits=hits,
            repo_name=repo_name,
            question="What is the architecture of this repository?",
        )

    def explain_code_purpose(
        self,
        repo_name: str,
        hits: list[RetrievalHit],
    ) -> ExplanationResult:
        context = format_retrieved_context(hits)
        prompt = build_code_purpose_prompt(repo_name, context)
        answer = self.llm.complete(prompt)
        return ExplanationResult(
            answer=answer,
            referenced_files=self.referenced_files(hits),
            retrieval_hits=hits,
            repo_name=repo_name,
            question="What is the main purpose of this codebase?",
        )

    def explain_file_responsibilities(
        self,
        repo_name: str,
        hits: list[RetrievalHit],
    ) -> ExplanationResult:
        context = format_retrieved_context(hits)
        prompt = build_file_responsibilities_prompt(repo_name, context)
        answer = self.llm.complete(prompt)
        return ExplanationResult(
            answer=answer,
            referenced_files=self.referenced_files(hits),
            retrieval_hits=hits,
            repo_name=repo_name,
            question="What are the responsibilities of the main files?",
        )

    def explain_file_intelligence(
        self,
        repo_name: str,
        file_path: str,
        context: str,
    ) -> str:
        """Generate structured per-file analysis from pre-built RAG context."""
        prompt = build_file_intelligence_prompt(repo_name, file_path, context)
        return self.llm.complete(prompt, max_tokens=2500)

    def summarize_chunks(
        self,
        repo_name: str,
        hits: list[RetrievalHit],
    ) -> ExplanationResult:
        context = format_retrieved_context(hits)
        prompt = build_chunk_summary_prompt(repo_name, context)
        answer = self.llm.complete(prompt)
        return ExplanationResult(
            answer=answer,
            referenced_files=self.referenced_files(hits),
            retrieval_hits=hits,
            repo_name=repo_name,
            question="Summarize the retrieved code chunks.",
        )
