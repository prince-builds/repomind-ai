"""Analyze import relationships and produce architecture insights."""

from dataclasses import dataclass
from pathlib import Path

from repomind.architecture.dependency_graph import DependencyGraph
from repomind.architecture.dependency_resolver import (
    IMPORT_EXTENSIONS,
    build_dependency_graph,
)

# Common entry-point filenames
ENTRY_POINT_NAMES = {
    "main.py",
    "app.py",
    "__main__.py",
    "index.js",
    "index.ts",
    "index.tsx",
    "main.ts",
    "main.js",
    "server.js",
    "server.ts",
    "app.js",
    "app.tsx",
}


class ArchitectureAnalysisError(Exception):
    """Raised when architecture analysis cannot complete."""


@dataclass(frozen=True)
class FileConnection:
    """Connection statistics for one file."""

    file_path: str
    inbound: int
    outbound: int
    total: int


@dataclass(frozen=True)
class ArchitectureReport:
    """Structured architecture analysis results."""

    repo_name: str
    files_analyzed: int
    graph: DependencyGraph
    top_connected: list[FileConnection]
    entry_points: list[str]

    @property
    def internal_dependencies(self) -> int:
        return self.graph.internal_edge_count

    @property
    def external_imports(self) -> int:
        return self.graph.external_import_count

    def to_context_text(self) -> str:
        """Format report as readable text."""
        lines = [
            f"Repository: {self.repo_name}",
            f"Files analyzed for imports: {self.files_analyzed}",
            f"Internal dependencies: {self.internal_dependencies}",
            f"External imports: {self.external_imports}",
            "",
            "Possible entry points:",
        ]

        if self.entry_points:
            lines.extend(f"  - {path}" for path in self.entry_points[:15])
        else:
            lines.append("  (none detected)")

        lines.append("")
        lines.append("Most connected files:")

        for conn in self.top_connected[:10]:
            lines.append(
                f"  - {conn.file_path} "
                f"(Inbound={conn.inbound}, "
                f"Outbound={conn.outbound}, "
                f"Total={conn.total})"
            )

        return "\n".join(lines)


def analyze_repository(
    repo_root: Path,
    scanned_files: list[Path],
    repo_name: str,
) -> ArchitectureReport:
    """
    Build dependency graph from repository imports.
    """
    repo_root = Path(repo_root).resolve()

    graph = build_dependency_graph(repo_root, scanned_files)

    code_files = [
        rel
        for rel in scanned_files
        if rel.suffix.lower() in IMPORT_EXTENSIONS
    ]

    top_raw = graph.top_connected_files(limit=10)

    top_connected = [
        FileConnection(path, inbound, outbound, total)
        for path, inbound, outbound, total in top_raw
    ]

    entry_points = graph.entry_point_candidates(ENTRY_POINT_NAMES)

    return ArchitectureReport(
        repo_name=repo_name,
        files_analyzed=len(code_files),
        graph=graph,
        top_connected=top_connected,
        entry_points=entry_points,
    )


def generate_architecture_summary(
    report: ArchitectureReport,
) -> str:
    """
    Generate an AI architecture summary via Groq from static analysis context.
    """
    from repomind.llm.explainer import LLMExplainer
    from repomind.llm.prompts import build_architecture_analysis_prompt

    context_parts = [report.to_context_text()]

    edges = report.graph.internal_edges()
    if edges:
        context_parts.append("")
        context_parts.append("Sample internal dependencies (source → target):")
        for edge in edges[:30]:
            context_parts.append(f"  - {edge.source} → {edge.target}")
        if len(edges) > 30:
            context_parts.append(f"  … and {len(edges) - 30} more edges")

    analysis_context = "\n".join(context_parts)
    prompt = build_architecture_analysis_prompt(report.repo_name, analysis_context)

    llm = LLMExplainer()
    return llm.complete(prompt, max_tokens=800)