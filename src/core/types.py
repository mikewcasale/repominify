"""Core types and data structures for repo-minify.

This module defines the fundamental data types and structures used throughout
the repo-minify package.

Version Compatibility:
    - Python 3.7+: Full support for all types
    - Python 3.6: Not supported (uses dataclasses)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Any

# Type aliases for graph operations
NodeID = str
NodeData = Dict[str, str]
EdgeData = Dict[str, str]
GraphData = Dict[str, List[Dict[str, str]]]


@dataclass
class FileEntry:
    """Container for file information from Repomix output.

    Attributes:
        path: File path relative to repository root
        content: File content as string
        size: Content size in bytes
        line_count: Number of lines in content
    """

    path: str
    content: str
    size: int = field(init=False)
    line_count: int = field(init=False)

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        self.size = len(self.content.encode("utf-8"))
        self.line_count = len(self.content.splitlines())

    def __str__(self) -> str:
        return (
            f"FileEntry(path='{self.path}', size={self.size}B, lines={self.line_count})"
        )


# Custom exceptions
class GraphBuildError(Exception):
    """Base exception for graph building errors."""

    pass


class FileParseError(GraphBuildError):
    """Raised when Repomix file parsing fails."""

    pass


class ValidationError(GraphBuildError):
    """Raised when input validation fails."""

    pass


# Performance tracking type
Stats = Dict[str, Any]
