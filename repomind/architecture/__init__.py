"""Infer and describe repository architecture."""

from repomind.architecture.architecture_analyzer import (
    ArchitectureAnalysisError,
    ArchitectureReport,
    analyze_repository,
    generate_architecture_summary,
)
from repomind.architecture.dependency_graph import DependencyEdge, DependencyGraph

__all__ = [
    "ArchitectureAnalysisError",
    "ArchitectureReport",
    "DependencyEdge",
    "DependencyGraph",
    "analyze_repository",
    "generate_architecture_summary",
]
