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


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global */
html, body, [class*="css"]  {
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

/* Reduce top whitespace (header + container padding) */
header[data-testid="stHeader"] { height: 0rem; }
div[data-testid="stToolbar"] { visibility: hidden; height: 0%; position: fixed; }
div[data-testid="stDecoration"] { visibility: hidden; height: 0%; position: fixed; }
.block-container {
  /* Target ~12px top padding */
  padding-top: 0.75rem;
  padding-bottom: 2.4rem;
  max-width: 1400px;
}

/* Streamlit sometimes applies padding higher up; normalize it */
div[data-testid="stAppViewContainer"] > .main {
  padding-top: 0rem !important;
}

/* Ensure the hero (first content) sits at the top */
.block-container > div:first-child { margin-top: 0rem !important; }
.stMarkdown { margin-top: 0rem; }

/* App background */
.stApp {
  background:
    radial-gradient(900px 600px at 18% 10%, rgba(124, 92, 255, 0.22), transparent 60%),
    /* reduced cyan glow ~40% */
    radial-gradient(900px 600px at 88% 22%, rgba(41, 210, 247, 0.07), transparent 55%),
    radial-gradient(900px 600px at 50% 92%, rgba(0, 255, 164, 0.06), transparent 50%),
    linear-gradient(180deg, #070A12 0%, #070A12 40%, #060915 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: rgba(10, 12, 24, 0.55);
  border-right: 1px solid rgba(255,255,255,0.08);
  backdrop-filter: blur(18px);
}

/* Glass cards */
.rm-card {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow:
    0 18px 45px rgba(0,0,0,0.40),
    0 1px 0 rgba(255,255,255,0.04) inset;
  backdrop-filter: blur(16px);
}
.rm-card + .rm-card { margin-top: 12px; }

/* Glass for Streamlit bordered containers (real containers, not HTML placeholders) */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.10) !important;
  border-radius: 18px !important;
  box-shadow:
    0 18px 45px rgba(0,0,0,0.40),
    0 1px 0 rgba(255,255,255,0.04) inset !important;
  backdrop-filter: blur(16px) !important;
}

/* Hero */
.rm-hero {
  padding: 8px 14px 8px 14px;
}
.rm-title {
  font-size: 32px;
  line-height: 1.15;
  font-weight: 700;
  margin: 0 0 4px 0;
  letter-spacing: -0.02em;
}
.rm-subtitle {
  margin: 2px 0 0 0;
  color: rgba(255,255,255,0.78);
  font-size: 15px;
  line-height: 1.55;
}
.rm-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.82);
  font-size: 12px;
}

/* Typography hierarchy (Streamlit markdown headings) */
.stMarkdown h2 {
  font-size: 20px;
  letter-spacing: -0.01em;
  margin-top: 0.5rem;
  margin-bottom: 0.6rem;
}
.stMarkdown h3 {
  font-size: 16px;
  letter-spacing: -0.01em;
  margin-top: 0.4rem;
  margin-bottom: 0.5rem;
}
.stMarkdown p, .stMarkdown li {
  color: rgba(255,255,255,0.82);
}
.stCaption, .stMarkdown small, .stMarkdown code {
  color: rgba(255,255,255,0.72);
}

/* Metric cards */
.rm-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.rm-metric {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 16px;
  padding: 14px 14px 13px 14px;
  backdrop-filter: blur(14px);
  box-shadow:
    0 16px 35px rgba(0,0,0,0.30),
    0 1px 0 rgba(255,255,255,0.04) inset;
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}
.rm-metric:hover {
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.16);
  box-shadow:
    0 20px 48px rgba(0,0,0,0.40),
    0 0 0 1px rgba(124, 92, 255, 0.10),
    0 1px 0 rgba(255,255,255,0.05) inset;
}
.rm-metric-label {
  color: rgba(255,255,255,0.70);
  font-size: 12px;
  margin-bottom: 6px;
}
.rm-metric-value {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.rm-metric-hint {
  color: rgba(255,255,255,0.62);
  font-size: 12px;
  margin-top: 6px;
}

/* Streamlit widgets tweaks */
div[data-testid="stExpander"] details {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
}
div[data-testid="stExpander"] details summary {
  padding: 10px 12px;
}

/* Inputs/buttons: softer + more premium */
div[data-baseweb="input"] > div {
  background: rgba(255,255,255,0.04) !important;
  border-color: rgba(255,255,255,0.12) !important;
  border-radius: 12px !important;
}
div[data-baseweb="textarea"] textarea {
  background: rgba(255,255,255,0.04) !important;
  border-color: rgba(255,255,255,0.12) !important;
  border-radius: 12px !important;
}
button[kind="primary"] {
  box-shadow: 0 12px 28px rgba(124, 92, 255, 0.22);
}
button:hover {
  filter: brightness(1.02);
}

/* Tabs spacing + look */
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 10px;
  margin-top: 0.25rem;
  padding: 4px 4px;
}
div[data-testid="stTabs"] [data-baseweb="tab"] {
  border-radius: 999px;
}

@media (max-width: 1100px) {
  .rm-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (min-width: 1800px) {
  .block-container { max-width: 1600px; }
}
</style>
"""


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


def _render_metric_cards(items: list[tuple[str, str, str | None]]) -> None:
    """
    Render metric cards in a glass grid.

    items: list of (label, value, hint)
    """
    cards = []
    for label, value, hint in items:
        hint_html = f'<div class="rm-metric-hint">{hint}</div>' if hint else ""
        cards.append(
            f"""
            <div class="rm-metric">
              <div class="rm-metric-label">{label}</div>
              <div class="rm-metric-value">{value}</div>
              {hint_html}
            </div>
            """
        )
    st.markdown(
        f'<div class="rm-metrics">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def _render_overview_tab(result: AnalysisResult) -> None:
    """Premium summary dashboard built from existing analysis output."""
    info = result.ingestion.clone.repo_info
    status = "Cloned" if result.ingestion.clone.was_cloned else "Loaded from cache"

    with st.container(border=True):
        st.markdown(f"### Repository\n**`{info.full_name}`**  \n{status}")
        st.markdown(f"**Local path:** `{result.ingestion.clone.local_path}`")

    # High-level structure metrics
    vectors = 0
    if result.retriever and result.retriever.is_ready:
        vectors = result.retriever.store.size

    entry_points = 0
    internal_deps = 0
    external_imports = 0
    files_analyzed = 0
    if result.architecture:
        entry_points = len(result.architecture.entry_points)
        internal_deps = result.architecture.internal_dependencies
        external_imports = result.architecture.external_imports
        files_analyzed = result.architecture.files_analyzed

    # Lightweight, UI-side estimates for classes/functions
    classes_detected = 0
    functions_detected = 0
    for parsed in result.parse_summary.parsed_files:
        text = parsed.content
        classes_detected += text.count("class ")
        functions_detected += text.count("def ") + text.count("function ")

    dependencies_found = internal_deps + external_imports

    _render_metric_cards(
        [
            ("Files indexed", str(len(result.parse_summary.parsed_files)), "Parsed into the index"),
            ("Chunks created", str(len(result.chunks)), "Text slices for retrieval"),
            ("Dependencies found", str(dependencies_found), "Internal + external imports"),
            ("Classes detected", str(classes_detected), "Heuristic count from parsed files"),
            ("Functions detected", str(functions_detected), "Heuristic count from parsed files"),
            ("Entry points", str(entry_points), "Likely starting files"),
        ]
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        with st.container(border=True):
            st.markdown("### Architecture summary (AI)")
            if result.architecture_summary:
                st.markdown(result.architecture_summary)
            else:
                st.info(
                    f"{MISSING_GROQ_KEY_MESSAGE} to generate an AI architecture summary."
                )
                if result.architecture:
                    with st.expander("Raw analysis context"):
                        st.code(result.architecture.to_context_text())

    with c2:
        with st.container(border=True):
            st.markdown("### Indexing snapshot")
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            st.caption(f"Supported parse types: {supported}")
            if result.chunks:
                with st.expander("Chunk preview (first 3)", expanded=False):
                    for chunk in result.chunks[:3]:
                        st.markdown(
                            f"**`{chunk.file_path}`** · chunk `{chunk.chunk_index}` · "
                            f"{chunk.char_count} chars"
                        )
                        st.code(chunk.content[:400] + ("…" if len(chunk.content) > 400 else ""))
                        st.divider()
            else:
                st.warning("No chunks were created for this repository.")


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
    st.markdown("### File Intelligence")
    st.caption(
        "Browse files and generate purpose, structure, dependencies, data flow, "
        "interview questions, and improvement ideas."
    )

    paths = sorted(path.as_posix() for path in result.ingestion.files)
    if not paths:
        st.info("No scanned files available.")
        return

    col_tree, col_detail = st.columns([1, 2])

    with col_tree:
        with st.container(border=True):
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

        with st.container(border=True):
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
    """Overview, Architecture, Files, Q&A, and Interview tabs after indexing."""
    repo_name = result.ingestion.clone.repo_info.full_name
    tab_overview, tab_arch, tab_files, tab_qa, tab_interview = st.tabs(
        ["📊 Overview", "🏗 Architecture", "📁 Files", "💬 Q&A", "🎯 Interview"]
    )

    with tab_overview:
        _render_overview_tab(result)

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

    with tab_interview:
        st.subheader("Interview pack")
        st.caption("Generate interview questions and discussion prompts from the indexed repository context.")

        if not (result.retriever and result.retriever.is_ready):
            st.warning(
                "Search index was not built. Interview pack requires embedded chunks."
            )
            return

        preset = st.selectbox(
            "Template",
            options=[
                "System design interview questions (repo-wide)",
                "Code review prompts (repo-wide)",
                "Architecture deep dive questions",
            ],
            index=0,
            key="interview_template",
        )
        if preset == "System design interview questions (repo-wide)":
            default_q = (
                "Generate a structured interview pack for this repository: "
                "5 system design questions, 5 code-reading questions, and 5 debugging scenarios. "
                "For each, include what a strong answer should cover. "
                "Cite file paths when relevant."
            )
        elif preset == "Code review prompts (repo-wide)":
            default_q = (
                "Create code review prompts for this repository: "
                "areas to scrutinize, questions to ask, risks to check (security/perf/maintainability), "
                "and suggested follow-ups. Cite file paths."
            )
        else:
            default_q = (
                "Create an architecture interview pack for this repository: "
                "components, data flow, failure modes, trade-offs, and scaling concerns. "
                "Include 8–12 questions and a brief rubric. Cite file paths."
            )

        question = st.text_area(
            "Prompt",
            value=default_q,
            height=140,
            key="interview_prompt",
        )
        top_k = st.slider(
            "Retrieved chunks",
            min_value=3,
            max_value=12,
            value=7,
            key="interview_top_k",
        )
        if st.button("Generate interview pack", type="primary", key="gen_interview"):
            if not question.strip():
                st.warning("Enter a prompt first.")
            else:
                explanation = _search_and_explain(result.retriever, repo_name, question.strip(), top_k)
                if explanation:
                    st.session_state["last_interview_pack"] = explanation
                    st.subheader("Interview output")
                    st.markdown(explanation.answer)
                    st.subheader("Referenced files")
                    for path in explanation.referenced_files:
                        st.markdown(f"- `{path}`")
                    _render_retrieved_context(explanation.retrieval_hits)
        elif st.session_state.get("last_interview_pack"):
            st.caption("Showing your last generated interview pack. Generate again to refresh.")
            explanation: ExplanationResult = st.session_state["last_interview_pack"]
            st.subheader("Interview output")
            st.markdown(explanation.answer)
            st.subheader("Referenced files")
            for path in explanation.referenced_files:
                st.markdown(f"- `{path}`")
            _render_retrieved_context(explanation.retrieval_hits)


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
    st.set_page_config(
        page_title="RepoMind AI",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    # Sidebar navigation (UX) + quick actions
    st.sidebar.markdown(
        f"""
        <div class="rm-card">
          <div class="rm-badge" style="font-size:11px; padding:4px 9px;">
            RepoMind AI <span style="opacity:.7; font-size:10px;">v{__version__}</span>
          </div>
          <div style="height:8px;"></div>
          <div style="font-weight:600; font-size:13px;">Navigation</div>
          <div style="color:rgba(255,255,255,.70); font-size:12px; margin-top:6px;">
            Use tabs in the main view. Keep this sidebar for quick actions.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Clear cached analysis", use_container_width=True):
        for key in (
            "analysis",
            "repo_name",
            "last_explanation",
            "last_file_analysis",
            "selected_file",
            "last_interview_pack",
        ):
            st.session_state.pop(key, None)
        st.sidebar.success("Cleared session state.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Tips**")
    st.sidebar.caption(
        "Set `GROQ_API_KEY` in `.env` for AI summaries, Q&A, and File Intelligence."
    )

    # Hero
    st.markdown(
        f"""
        <div class="rm-card rm-hero">
          <div class="rm-badge">Repository Intelligence • Architecture • Q&A • File Intelligence</div>
          <div style="height:6px;"></div>
          <div class="rm-title">RepoMind AI</div>
          <p class="rm-subtitle">
            Understand any GitHub repository: clone, index, map architecture, browse files, and ask precise questions —
            all in one premium workspace.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        repo_url = st.text_input(
            "GitHub repository URL",
            placeholder="https://github.com/owner/repo",
            help="Public repos work without a token. Set GITHUB_TOKEN in .env for private repos.",
            label_visibility="collapsed",
        )
        col_a, col_b, col_c = st.columns([1.2, 1, 1])
        with col_a:
            st.caption("Paste a GitHub URL and analyze to build an in-memory search index.")
        with col_b:
            analyze_clicked = st.button(
                "Analyze repository", type="primary", use_container_width=True
            )
        with col_c:
            st.caption("Dark UI • Glass cards • Sidebar actions")

    if analyze_clicked:
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
        # Keep the functional sections available (now behind a premium dashboard + tabs).
        # with st.expander("Ingestion details", expanded=False):
        #     _render_ingestion_section(result)
        # with st.expander("Parsing & chunking details", expanded=False):
        #     _render_parse_chunk_section(result)
        _render_analysis_workspace(result)

    elif st.session_state.get("analysis"):
        cached: AnalysisResult = st.session_state["analysis"]
        repo_name = st.session_state.get("repo_name", "repository")
        st.info(f"Using indexed data for **{repo_name}**. Analyze again to refresh.")
        _render_analysis_workspace(cached)
