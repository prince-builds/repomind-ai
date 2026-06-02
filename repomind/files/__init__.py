"""File tree and per-file intelligence analysis."""

from repomind.files.file_intelligence import (
    FileIntelligenceResult,
    analyze_file,
    gather_file_hits,
)
from repomind.files.file_tree import build_file_tree, filter_paths, flatten_tree_paths

__all__ = [
    "FileIntelligenceResult",
    "analyze_file",
    "gather_file_hits",
    "build_file_tree",
    "filter_paths",
    "flatten_tree_paths",
]
