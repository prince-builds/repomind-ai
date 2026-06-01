"""Dependency graph data structure and metrics."""

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DependencyEdge:
    """One directed dependency between two files."""

    source: str
    target: str
    is_internal: bool


@dataclass
class DependencyGraph:
    """
    Directed graph of file-to-file dependencies.

    Nodes are repository-relative file paths (forward slashes).
    """

    edges: list[DependencyEdge] = field(default_factory=list)
    _outbound: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    _inbound: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    external_import_count: int = 0

    def add_internal_edge(self, source: str, target: str) -> None:
        """Record a dependency between two files in the repository."""
        if source == target:
            return
        self.edges.append(DependencyEdge(source, target, is_internal=True))
        self._outbound[source].add(target)
        self._inbound[target].add(source)

    def record_external_import(self) -> None:
        """Count an import that does not resolve to a project file."""
        self.external_import_count += 1

    @property
    def internal_edge_count(self) -> int:
        return sum(1 for edge in self.edges if edge.is_internal)

    def nodes(self) -> set[str]:
        """All files that participate in the graph."""
        all_nodes: set[str] = set()
        for edge in self.edges:
            if edge.is_internal:
                all_nodes.add(edge.source)
                all_nodes.add(edge.target)
        return all_nodes

    def inbound_count(self, file_path: str) -> int:
        return len(self._inbound.get(file_path, set()))

    def outbound_count(self, file_path: str) -> int:
        return len(self._outbound.get(file_path, set()))

    def outbound_targets(self, file_path: str) -> list[str]:
        """Return sorted internal files this file imports (outbound edges)."""
        return sorted(self._outbound.get(file_path, set()))

    def inbound_sources(self, file_path: str) -> list[str]:
        """Return sorted internal files that import this file (inbound edges)."""
        return sorted(self._inbound.get(file_path, set()))

    def connection_count(self, file_path: str) -> int:
        return self.inbound_count(file_path) + self.outbound_count(file_path)

    def top_connected_files(self, limit: int = 10) -> list[tuple[str, int, int, int]]:
        """
        Return files sorted by total connections.

        Each tuple: (file_path, inbound, outbound, total).
        """
        scored: list[tuple[str, int, int, int]] = []
        for node in self.nodes():
            inbound = self.inbound_count(node)
            outbound = self.outbound_count(node)
            total = inbound + outbound
            scored.append((node, inbound, outbound, total))

        scored.sort(key=lambda item: item[3], reverse=True)
        return scored[:limit]

    def internal_edges(self) -> list[DependencyEdge]:
        return [edge for edge in self.edges if edge.is_internal]

    def entry_point_candidates(
        self,
        known_entry_names: set[str] | None = None,
    ) -> list[str]:
        """
        Guess entry points: common filenames or files with outbound but no inbound edges.
        """
        names = known_entry_names or {
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

        candidates: list[str] = []
        for node in self.nodes():
            basename = node.rsplit("/", 1)[-1]
            if basename in names:
                candidates.append(node)

        # Files that import others but are rarely imported themselves
        for node in self.nodes():
            if self.inbound_count(node) == 0 and self.outbound_count(node) > 0:
                if node not in candidates:
                    candidates.append(node)

        return sorted(set(candidates))

    def to_dot(self, max_edges: int = 40) -> str:
        """Build a Graphviz DOT representation (optional visualization)."""
        lines = ["digraph dependencies {", '  rankdir="LR";', "  node [shape=box];"]
        shown = self.internal_edges()[:max_edges]
        for edge in shown:
            src = edge.source.replace('"', '\\"')
            tgt = edge.target.replace('"', '\\"')
            lines.append(f'  "{src}" -> "{tgt}";')
        if len(self.internal_edges()) > max_edges:
            lines.append("  // … truncated …")
        lines.append("}")
        return "\n".join(lines)
