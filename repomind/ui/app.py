"""Main Streamlit layout."""

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from repomind import __version__
from repomind.architecture.architecture_analyzer import (
    ArchitectureReport,
    analyze_repository,
    generate_architecture_summary,
)
from repomind.chunking.chunker import TextChunk, chunk_parsed_files
from repomind.embeddings.embedder import EmbeddingError
from repomind.explanations.repository_explainer import ExplanationResult, RepositoryExplainer
from repomind.files.file_intelligence import FileIntelligenceResult, analyze_file
from repomind.files.file_tree import build_file_tree, filter_paths
from repomind.ingestion.file_scanner import scan_repository
from repomind.ingestion.github_loader import (
    CloneResult,
    GitHubURLError,
    clone_github_repo,
    parse_github_url,
)
from repomind.llm.explainer import (
    LLMConfigError,
    LLMError,
    MISSING_GROQ_KEY_MESSAGE,
)
from repomind.parsing.parser import ParseSummary, parse_repository
from repomind.parsing.supported_types import SUPPORTED_EXTENSIONS
from repomind.retrieval.retriever import RetrievalHit, Retriever
from repomind.retrieval.vector_store import VectorStoreError


@dataclass(frozen=True)
class IngestionResult:
    """Summary of clone + file scan."""

    clone: CloneResult
    files: list[Path]


@dataclass(frozen=True)
class AnalysisResult:
    """Full pipeline through embeddings, FAISS indexing, and architecture."""

    ingestion: IngestionResult
    parse_summary: ParseSummary
    chunks: list[TextChunk]
    retriever: Retriever | None
    embedding_dim: int
    architecture: ArchitectureReport | None
    architecture_summary: str | None


def _run_analysis(repo_url: str) -> AnalysisResult:
    """Clone, scan, parse, chunk, embed, and index a repository."""
    clone_result = clone_github_repo(repo_url)
    repo_name = clone_result.repo_info.full_name
    local_path = clone_result.local_path

    scanned_files = scan_repository(local_path)
    parse_summary = parse_repository(local_path, scanned_files, repo_name)
    chunks = chunk_parsed_files(parse_summary.parsed_files)

    retriever: Retriever | None = None
    embedding_dim = 0

    if chunks:
        retriever = Retriever()
        retriever.build_index(chunks)
        embedding_dim = retriever.store.embedding_dim

    architecture = analyze_repository(local_path, scanned_files, repo_name)
    architecture_summary: str | None = None
    try:
        architecture_summary = generate_architecture_summary(architecture)
    except LLMConfigError:
        architecture_summary = None
    except LLMError:
        architecture_summary = None

    ingestion = IngestionResult(clone=clone_result, files=scanned_files)
    return AnalysisResult(
        ingestion=ingestion,
        parse_summary=parse_summary,
        chunks=chunks,
        retriever=retriever,
        embedding_dim=embedding_dim,
        architecture=architecture,
        architecture_summary=architecture_summary,
    )


def _save_analysis_to_session(result: AnalysisResult) -> None:
    """Keep retriever and repo context for follow-up questions."""
    st.session_state["analysis"] = result
    st.session_state["repo_name"] = result.ingestion.clone.repo_info.full_name


def _render_ingestion_section(result: AnalysisResult) -> None:
    """Show clone and scan summary."""
    ingestion = result.ingestion
    info = ingestion.clone.repo_info
    status = "cloned" if ingestion.clone.was_cloned else "loaded from cache"
    st.success(f"Repository **{info.full_name}** {status}.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Repository", info.full_name)
    with col2:
        st.metric("Scanned files", len(ingestion.files))
    with col3:
        st.metric("Parsed files", len(result.parse_summary.parsed_files))

    st.subheader("Storage")
    st.text(str(ingestion.clone.local_path))

    if ingestion.files:
        with st.expander("Scanned files (first 20)"):
            preview = ingestion.files[:20]
            st.code("\n".join(str(p) for p in preview), language=None)
            if len(ingestion.files) > 20:
                st.caption(f"Showing 20 of {len(ingestion.files)} scanned files.")


def _render_parse_chunk_section(result: AnalysisResult) -> None:
    """Show parsing, chunking, and embedding statistics."""
    summary = result.parse_summary
    chunks = result.chunks

    st.subheader("Parsing & chunking")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Parsed files", len(summary.parsed_files))
    with col2:
        st.metric("Total chunks", len(chunks))
    with col3:
        st.metric("Skipped (unsupported)", summary.skipped_unsupported)
    with col4:
        st.metric("Skipped (unreadable)", summary.skipped_unreadable)

    if not chunks:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        st.warning(
            "No chunks were created. Try a repo with supported text files: "
            f"{supported}"
        )
        return

    st.subheader("Embeddings & search index")
    if result.retriever and result.retriever.is_ready:
        st.metric("Vectors indexed", result.retriever.store.size)
        if result.embedding_dim:
            st.caption(
                f"Embedding model: all-MiniLM-L6-v2 "
                f"({result.embedding_dim} dimensions)"
            )
    else:
        st.warning("Search index was not built.")

    st.subheader("Chunk preview (first 5)")
    for chunk in chunks[:5]:
        with st.expander(
            f"{chunk.file_path} — chunk {chunk.chunk_index} "
            f"({chunk.char_count} chars)",
            expanded=False,
        ):
            st.markdown(
                f"**Repo:** `{chunk.repo_name}`  \n"
                f"**File:** `{chunk.file_path}`  \n"
                f"**Chunk index:** `{chunk.chunk_index}`  \n"
                f"**Characters:** `{chunk.char_count}`"
            )
            st.code(chunk.content[:500] + ("…" if len(chunk.content) > 500 else ""))

    if len(chunks) > 5:
        st.caption(f"Showing 5 of {len(chunks)} chunks.")


def _render_architecture_section(result: AnalysisResult) -> None:
    """Show dependency analysis and LLM architecture summary."""
    report = result.architecture
    if report is None:
        return

    st.subheader("Architecture analysis")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Files analyzed", report.files_analyzed)
    with col2:
        st.metric("Internal dependencies", report.internal_dependencies)
    with col3:
        st.metric("External imports", report.external_imports)
    with col4:
        st.metric("Entry points", len(report.entry_points))

    if report.top_connected:
        st.markdown("**Top connected files**")
        chart_data = {conn.file_path: conn.total for conn in report.top_connected}
        st.bar_chart(chart_data)

        table_rows = [
            {
                "File": conn.file_path,
                "Inbound": conn.inbound,
                "Outbound": conn.outbound,
                "Total": conn.total,
            }
            for conn in report.top_connected
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No internal import relationships detected in Python/JS/TS files.")

    if report.entry_points:
        st.markdown("**Possible entry points**")
        for path in report.entry_points:
            st.markdown(f"- `{path}`")

    with st.expander("Dependency details", expanded=False):
        edges = report.graph.internal_edges()
        if not edges:
            st.caption("No internal edges to display.")
        else:
            st.caption(f"Showing up to 50 of {len(edges)} dependencies.")
            edge_rows = [
                {"From": e.source, "To": e.target} for e in edges[:50]
            ]
            st.dataframe(edge_rows, use_container_width=True, hide_index=True)

        st.markdown("**Graph (Graphviz DOT)**")
        st.code(report.graph.to_dot(max_edges=40), language=None)
        try:
            st.graphviz_chart(report.graph.to_dot(max_edges=25))
        except Exception:
            st.caption(
                "Install Graphviz on your system to see the network diagram here."
            )

    st.subheader("Architecture summary (AI)")
    if result.architecture_summary:
        st.markdown(result.architecture_summary)
    else:
        st.info(
            f"{MISSING_GROQ_KEY_MESSAGE} to generate an AI architecture summary."
        )
        with st.expander("Raw analysis context"):
            st.code(report.to_context_text())


def _render_retrieved_context(hits: list[RetrievalHit]) -> None:
    """Expandable section showing raw retrieval results."""
    with st.expander("Retrieved Context", expanded=False):
        if not hits:
            st.caption("No chunks were retrieved.")
            return

        for rank, hit in enumerate(hits, start=1):
            preview = hit.content[:400] + ("…" if len(hit.content) > 400 else "")
            st.markdown(
                f"**#{rank}** `{hit.file_path}` · chunk `{hit.chunk_index}` · "
                f"score `{hit.score:.4f}`"
            )
            st.code(preview)
            st.divider()


def _render_explanation(explanation: ExplanationResult) -> None:
    """Show LLM answer, referenced files, and retrieval context."""
    st.subheader("AI explanation")
    st.markdown(explanation.answer)

    st.subheader("Referenced files")
    if explanation.referenced_files:
        for path in explanation.referenced_files:
            st.markdown(f"- `{path}`")
    else:
        st.caption("No files referenced.")

    _render_retrieved_context(explanation.retrieval_hits)


def _search_and_explain(
    retriever: Retriever,
    repo_name: str,
    question: str,
    top_k: int,
) -> ExplanationResult | None:
    """Retrieve chunks, then generate an LLM explanation."""
    with st.spinner("Searching and generating explanation…"):
        try:
            hits = retriever.query(question, top_k=top_k)
        except (EmbeddingError, VectorStoreError) as exc:
            st.error(str(exc))
            return None
        except Exception as exc:
            st.error(f"Search failed: {exc}")
            return None

        if not hits:
            st.info("No matching chunks found. Try a different question.")
            return None

        try:
            explainer = RepositoryExplainer()
            return explainer.explain_user_question(repo_name, question, hits)
        except LLMConfigError as exc:
            st.error(str(exc))
            st.info("Copy `.env.example` to `.env` and set `GROQ_API_KEY`.")
            return None
        except LLMError as exc:
            st.error(str(exc))
            return None
        except Exception as exc:
            st.error(f"Explanation failed: {exc}")
            return None


def _render_path_tree(tree: dict, *, key_prefix: str = "tree") -> None:
    """Nested expanders for folder navigation; sets session selected_file on click."""
    for name in sorted(tree.keys(), key=str.lower):
        value = tree[name]
        if isinstance(value, dict):
            with st.expander(name, expanded=False):
                _render_path_tree(value, key_prefix=f"{key_prefix}/{name}")
        elif isinstance(value, str):
            label = value.rsplit("/", 1)[-1]
            if st.button(
                label,
                key=f"{key_prefix}:{value}",
                help=value,
                use_container_width=True,
            ):
                st.session_state["selected_file"] = value


def _run_file_analysis(
    result: AnalysisResult,
    file_path: str,
) -> FileIntelligenceResult | None:
    """Generate per-file intelligence via Groq."""
    repo_name = result.ingestion.clone.repo_info.full_name
    repo_root = result.ingestion.clone.local_path
    graph = result.architecture.graph if result.architecture else None

    with st.spinner(f"Analyzing `{file_path}`…"):
        try:
            return analyze_file(
                repo_name=repo_name,
                repo_root=repo_root,
                file_path=file_path,
                chunks=result.chunks,
                graph=graph,
            )
        except LLMConfigError as exc:
            st.error(str(exc))
            st.info("Copy `.env.example` to `.env` and set `GROQ_API_KEY`.")
            return None
        except LLMError as exc:
            st.error(str(exc))
            return None
        except Exception as exc:
            st.error(f"File analysis failed: {exc}")
            return None


def _render_file_intelligence(result: FileIntelligenceResult) -> None:
    """Show structured file analysis and supporting context."""
    st.markdown(result.answer)

    if result.related_files:
        st.markdown("**Related files (dependency expansion)**")
        for path in result.related_files:
            st.markdown(f"- `{path}`")

    _render_retrieved_context(result.retrieval_hits)


def _render_files_section(result: AnalysisResult) -> None:
    """File tree sidebar and per-file Groq analysis."""
    st.subheader("File Intelligence")
    st.caption(
        "Browse repository files and generate purpose, structure, dependencies, "
        "data flow, interview questions, and improvement ideas."
    )

    paths = sorted(path.as_posix() for path in result.ingestion.files)
    if not paths:
        st.info("No scanned files available.")
        return

    col_tree, col_detail = st.columns([1, 2])

    with col_tree:
        query = st.text_input(
            "Filter files",
            placeholder="e.g. repomind/ui",
            key="files_filter",
        )
        filtered = filter_paths(paths, query)
        st.caption(f"{len(filtered)} of {len(paths)} files")

        st.markdown("**Browse**")
        if filtered:
            _render_path_tree(build_file_tree(filtered))
        else:
            st.caption("No files match the filter.")

        picker_options = ["— Select a file —", *filtered]
        pick_index = 0
        selected_file = st.session_state.get("selected_file")
        if selected_file in filtered:
            pick_index = picker_options.index(selected_file)

        picked = st.selectbox(
            "Quick select",
            options=picker_options,
            index=pick_index,
            key="files_picker",
        )
        if picked != "— Select a file —":
            st.session_state["selected_file"] = picked

    file_path = st.session_state.get("selected_file")
    if file_path and file_path not in paths:
        st.session_state.pop("selected_file", None)
        file_path = None

    with col_detail:
        if not file_path:
            st.info("Select a file from the tree or quick select list.")
            return

        st.markdown(f"**Selected file:** `{file_path}`")

        if st.button("Analyze file", type="primary", key="analyze_file_btn"):
            analysis = _run_file_analysis(result, file_path)
            if analysis:
                st.session_state["last_file_analysis"] = analysis
                _render_file_intelligence(analysis)
        elif cached := st.session_state.get("last_file_analysis"):
            if cached.file_path == file_path:
                st.caption("Showing your last analysis for this file. Analyze again to refresh.")
                _render_file_intelligence(cached)
            else:
                st.caption("Analyze this file to generate intelligence.")
        else:
            st.caption("Click **Analyze file** to generate intelligence.")


def _render_analysis_workspace(result: AnalysisResult) -> None:
    """Architecture, Files, and Q&A tabs after indexing."""
    repo_name = result.ingestion.clone.repo_info.full_name
    tab_arch, tab_files, tab_qa = st.tabs(["Architecture", "Files", "Q&A"])

    with tab_arch:
        _render_architecture_section(result)

    with tab_files:
        _render_files_section(result)

    with tab_qa:
        if result.retriever and result.retriever.is_ready:
            _render_query_section(result.retriever, repo_name)
        else:
            st.warning(
                "Search index was not built. Q&A requires embedded chunks from "
                "supported file types."
            )


def _render_query_section(retriever: Retriever, repo_name: str) -> None:
    """Natural-language search with automatic AI explanation."""
    st.subheader("Ask about this repository")
    st.caption(f"Semantic search + AI explanation for **{repo_name}**")

    question = st.text_input(
        "Ask about this repository",
        placeholder="How does authentication work?",
        key="repo_question",
        label_visibility="collapsed",
    )

    top_k = st.slider("Number of retrieved chunks", min_value=1, max_value=10, value=5)

    if st.button("Ask RepoMind", type="secondary"):
        if not question.strip():
            st.warning("Enter a question first.")
            return

        explanation = _search_and_explain(
            retriever, repo_name, question.strip(), top_k
        )
        if explanation:
            st.session_state["last_explanation"] = explanation
            _render_explanation(explanation)

    elif st.session_state.get("last_explanation"):
        st.caption("Showing your last answer. Ask again to refresh.")
        _render_explanation(st.session_state["last_explanation"])


def render_app() -> None:
    st.title("RepoMind AI")
    st.caption(f"v{__version__} — Understand any repository with AI")

    repo_url = st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repo",
        help="Public repos work without a token. Set GITHUB_TOKEN in .env for private repos.",
    )

    if st.button("Analyze repository", type="primary"):
        if not repo_url.strip():
            st.warning("Enter a repository URL.")
            return

        try:
            parse_github_url(repo_url)
        except GitHubURLError as exc:
            st.error(str(exc))
            return

        st.session_state.pop("last_explanation", None)
        st.session_state.pop("last_file_analysis", None)
        st.session_state.pop("selected_file", None)

        with st.spinner(
            "Cloning, scanning, parsing, chunking, indexing, and analyzing architecture…"
        ):
            try:
                result = _run_analysis(repo_url)
            except GitHubURLError as exc:
                st.error(str(exc))
                return
            except (EmbeddingError, VectorStoreError) as exc:
                st.error(str(exc))
                return
            except FileNotFoundError as exc:
                st.error(str(exc))
                return
            except ValueError as exc:
                st.error(str(exc))
                return
            except Exception as exc:
                st.error(f"Unexpected error during analysis: {exc}")
                return

        _save_analysis_to_session(result)
        _render_ingestion_section(result)
        _render_parse_chunk_section(result)
        _render_analysis_workspace(result)

    elif st.session_state.get("analysis"):
        cached: AnalysisResult = st.session_state["analysis"]
        repo_name = st.session_state.get("repo_name", "repository")
        st.info(f"Using indexed data for **{repo_name}**. Analyze again to refresh.")
        _render_analysis_workspace(cached)
