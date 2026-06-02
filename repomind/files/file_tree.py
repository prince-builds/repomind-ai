"""Build a nested path tree for repository file browsing."""

from __future__ import annotations

from typing import Any


def build_file_tree(paths: list[str]) -> dict[str, Any]:
    """
    Build a nested dict from posix file paths.

    Leaf nodes map the filename key to the full path string.
    Directory nodes map names to child dicts.
    """
    root: dict[str, Any] = {}
    for path in sorted(paths):
        parts = path.split("/")
        node = root
        for index, part in enumerate(parts):
            is_leaf = index == len(parts) - 1
            if is_leaf:
                node[part] = path
            else:
                child = node.setdefault(part, {})
                if isinstance(child, str):
                    # Rare collision: file and folder share a name segment
                    child = {part: child}
                    node[part] = child
                node = child
    return root


def flatten_tree_paths(tree: dict[str, Any], prefix: str = "") -> list[str]:
    """Collect all file paths from a tree (depth-first, sorted)."""
    paths: list[str] = []
    for key in sorted(tree.keys(), key=str.lower):
        value = tree[key]
        if isinstance(value, dict):
            paths.extend(flatten_tree_paths(value, f"{prefix}{key}/"))
        elif isinstance(value, str):
            paths.append(value)
    return paths


def filter_paths(paths: list[str], query: str) -> list[str]:
    """Case-insensitive substring filter on file paths."""
    cleaned = query.strip().lower()
    if not cleaned:
        return paths
    return [path for path in paths if cleaned in path.lower()]
