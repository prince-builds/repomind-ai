"""Resolve internal import relationships for Python, JavaScript, and TypeScript."""

import ast
import re
from pathlib import Path

from repomind.architecture.dependency_graph import DependencyGraph
from repomind.parsing.parser import read_text_file

# Files we parse for import statements (same as architecture analysis)
IMPORT_EXTENSIONS: frozenset[str] = frozenset({".py", ".js", ".ts", ".tsx", ".jsx"})

_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+(?:[\w*{}\s,]+\s+from\s+)?|export\s+[\w*{}\s,]+\s+from\s+)"""
    r"""['"]([^'"]+)['"]""",
    re.MULTILINE,
)
_JS_REQUIRE_RE = re.compile(
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)


def extract_python_imports(content: str) -> list[str]:
    """Extract module paths from Python import statements."""
    imports: list[str] = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
            elif node.level and node.level > 0:
                imports.append("." * node.level)

    return imports


def extract_javascript_imports(content: str) -> list[str]:
    """Extract module paths from JS/TS import and require statements."""
    imports: list[str] = []
    imports.extend(match.group(1) for match in _JS_IMPORT_RE.finditer(content))
    imports.extend(match.group(1) for match in _JS_REQUIRE_RE.finditer(content))
    return imports


def extract_imports(file_path: Path, content: str) -> list[str]:
    """Dispatch import extraction based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        return extract_python_imports(content)
    if suffix in {".js", ".ts", ".tsx", ".jsx"}:
        return extract_javascript_imports(content)
    return []


def build_file_index(repo_root: Path, code_files: list[Path]) -> dict[str, str]:
    """
    Map lookup keys to normalized repo-relative paths.

    Keys include full path, path without extension, and Python module path.
    """
    index: dict[str, str] = {}
    for rel in code_files:
        posix = rel.as_posix()
        index[posix] = posix
        stem_posix = rel.with_suffix("").as_posix()
        index[stem_posix] = posix
        if rel.suffix == ".py":
            module = stem_posix.replace("/", ".")
            index[module] = posix
    return index


def resolve_import(
    importer: Path,
    import_spec: str,
    file_index: dict[str, str],
) -> str | None:
    """
    Resolve an import string to a repo-relative file path, if internal.

    Returns None for external packages or unresolvable paths.
    """
    spec = import_spec.strip().strip('"').strip("'")
    if not spec or spec.startswith(("http://", "https://")):
        return None

    if not spec.startswith((".", "/")) and "/" not in spec and "\\" not in spec:
        if spec not in file_index:
            return None
        return file_index.get(spec)

    if spec.startswith("."):
        base_dir = importer.parent
        joined = (base_dir / spec).as_posix()
        for candidate in (
            joined,
            f"{joined}.py",
            f"{joined}.ts",
            f"{joined}.tsx",
            f"{joined}.js",
            f"{joined}.jsx",
            f"{joined}/index.py",
            f"{joined}/index.ts",
            f"{joined}/index.js",
        ):
            normalized = Path(candidate).as_posix()
            if normalized in file_index:
                return file_index[normalized]
        return None

    normalized = Path(spec).as_posix()
    for candidate in (
        normalized,
        f"{normalized}.py",
        f"{normalized}.ts",
        f"{normalized}.js",
    ):
        if candidate in file_index:
            return file_index[candidate]

    return file_index.get(spec.replace(".", "/"))


def build_dependency_graph(
    repo_root: Path,
    scanned_files: list[Path],
) -> DependencyGraph:
    """
    Parse imports in code files and return a dependency graph.

    Only files in scanned_files with supported extensions are considered.
    """
    repo_root = Path(repo_root).resolve()
    code_files = [
        rel for rel in scanned_files if rel.suffix.lower() in IMPORT_EXTENSIONS
    ]
    file_index = build_file_index(repo_root, code_files)
    graph = DependencyGraph()

    for rel in code_files:
        absolute = repo_root / rel
        content = read_text_file(absolute)
        if content is None:
            continue

        source_path = rel.as_posix()
        for import_spec in extract_imports(rel, content):
            target = resolve_import(rel, import_spec, file_index)
            if target:
                graph.add_internal_edge(source_path, target)
            else:
                graph.record_external_import()

    return graph


class DependencyResolver:
    """
    Maps each file to its internal import targets using the dependency graph.

    Retrieval and traversal stay separate: the graph is built once per repo scan.
    """

    def __init__(self, graph: DependencyGraph) -> None:
        self._graph = graph

    @classmethod
    def from_scanned(cls, repo_root: Path, scanned_files: list[Path]) -> "DependencyResolver":
        """Build resolver from repository root and scanned relative paths."""
        return cls(build_dependency_graph(repo_root, scanned_files))

    @property
    def graph(self) -> DependencyGraph:
        return self._graph

    def internal_import_targets(self, file_path: str) -> list[str]:
        """Return repo-relative paths this file imports (internal only)."""
        return self._graph.outbound_targets(file_path)

    def internal_importers(self, file_path: str) -> list[str]:
        """Return repo-relative paths that import this file."""
        return self._graph.inbound_sources(file_path)
