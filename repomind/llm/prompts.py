"""Reusable prompt templates for repository explanations."""

from repomind.retrieval.context_builder import NeighborSnippet
from repomind.retrieval.retriever import RetrievalHit

SYSTEM_PROMPT = """You are RepoMind AI, an expert software engineer who explains codebases clearly.

Rules:
- Base answers only on the provided repository context.
- If context is insufficient, say what is missing instead of guessing.
- Be concise, accurate, and beginner-friendly.
- Mention specific file paths when they support your answer.
"""


def format_retrieved_context(hits: list[RetrievalHit]) -> str:
    """Turn retrieval hits into a single context block for the LLM."""
    if not hits:
        return "(No retrieved context available.)"

    blocks: list[str] = []
    for index, hit in enumerate(hits, start=1):
        blocks.append(
            f"### Chunk {index}\n"
            f"- File: {hit.file_path}\n"
            f"- Chunk index: {hit.chunk_index}\n"
            f"- Similarity score: {hit.score:.4f}\n"
            f"- Content:\n{hit.content}"
        )
    return "\n\n".join(blocks)


def format_neighbor_snippets(
    snippets: tuple[NeighborSnippet, ...] | list[NeighborSnippet],
) -> str:
    """Format dependency-expanded neighbor files for the LLM."""
    if not snippets:
        return ""

    parts: list[str] = ["## Related context (dependency expansion)", ""]
    for snippet in snippets:
        parts.append(
            f"### File: {snippet.file_path} (graph depth {snippet.depth})\n"
            f"Characters included: {snippet.char_count}\n"
            f"```\n{snippet.content}\n```"
        )
        parts.append("")
    return "\n".join(parts).strip()


def combine_rag_context(
    primary_hits: list[RetrievalHit],
    neighbor_snippets: tuple[NeighborSnippet, ...] | list[NeighborSnippet] | None = None,
    dependency_outline: str | None = None,
) -> str:
    """
    Build full RAG context: primary chunks, optional import graph summary, neighbors.
    """
    sections: list[str] = [
        "## Primary retrieval (semantic search)",
        format_retrieved_context(primary_hits),
    ]

    if dependency_outline:
        sections.append("")
        sections.append("## Repository dependency outline (static analysis)")
        sections.append(dependency_outline.strip())

    neighbor_text = format_neighbor_snippets(neighbor_snippets or ())
    if neighbor_text:
        sections.append("")
        sections.append(neighbor_text)

    return "\n\n".join(sections)


def build_architecture_analysis_prompt(repo_name: str, analysis_context: str) -> str:
    """Prompt for summarizing dependency-graph architecture analysis."""
    return f"""Repository: {repo_name}

Dependency analysis (imports and file relationships):
{analysis_context}

Write a clear architecture summary for a developer new to this codebase.

Include:
1. High-level structure (layers, modules, or areas)
2. How key files connect (based on dependencies)
3. Likely entry points and what they start
4. Any hubs or highly connected files and why they matter

Keep it under 250 words. Use bullet points where helpful."""


def build_architecture_prompt(repo_name: str, context: str) -> str:
    """Prompt for high-level repository architecture."""
    return f"""Repository: {repo_name}

Retrieved code context:
{context}

Explain the overall architecture of this repository:
- main components and how they connect
- typical request or execution flow (if visible)
- important directories or modules

Keep the answer structured and under 300 words."""


def build_code_purpose_prompt(repo_name: str, context: str) -> str:
    """Prompt for what the codebase does."""
    return f"""Repository: {repo_name}

Retrieved code context:
{context}

Explain the main purpose of this codebase in plain language.
Describe what problem it solves and who might use it."""


def build_file_responsibilities_prompt(repo_name: str, context: str) -> str:
    """Prompt for file-level responsibilities."""
    return f"""Repository: {repo_name}

Retrieved code context:
{context}

Summarize the responsibilities of the files shown in the context.
Use a short bullet list: file path → responsibility."""


def build_chunk_summary_prompt(repo_name: str, context: str) -> str:
    """Prompt to summarize retrieved chunks."""
    return f"""Repository: {repo_name}

Retrieved code context:
{context}

Summarize the key ideas in these code chunks in 5–8 bullet points."""


def build_file_intelligence_prompt(
    repo_name: str,
    file_path: str,
    context: str,
) -> str:
    """Prompt for deep single-file analysis using indexed and dependency context."""
    return f"""Repository: {repo_name}
Target file: {file_path}

Context (indexed chunks, dependency graph, and related files):
{context}

Analyze **only** the target file `{file_path}` using the context above.

Respond in markdown with these exact section headings (use bullet lists where appropriate):

## Purpose
What this file is responsible for in the repository.

## Imports
Key imports/modules and why they matter for this file.

## Classes
Classes defined in this file (name → brief role). If none, state "None".

## Functions
Important functions/methods (name → brief role). If none, state "None".

## Dependencies
How this file relates to other project files (who imports it, what it imports).

## Data Flow
How data or control flows through this file (inputs, outputs, side effects).

## Interview Questions
3–5 technical interview questions a candidate could answer using this file.

## Potential Improvements
Concrete, actionable improvements (readability, structure, tests, performance).

Rules:
- Do not invent symbols or files not supported by the context.
- If a section lacks evidence, say what is missing instead of guessing.
- Keep each section focused; avoid repeating the same point across sections."""


def build_question_prompt(
    repo_name: str,
    question: str,
    context: str,
) -> str:
    """Prompt for answering a user question with RAG context (may include expansion)."""
    return f"""Repository: {repo_name}

User question:
{question}

Context (retrieval + optional dependency-expanded files):
{context}

Answer the user's question using the context above.

Your response must include:
1. A concise direct answer (2–4 short paragraphs max)
2. A "Referenced files" section listing file paths you relied on
3. Brief notes on each file's role when relevant

Do not invent files or behavior not supported by the context."""
