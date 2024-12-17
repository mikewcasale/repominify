"""Core types and data structures for repo-minify.

This module defines the fundamental data types and structures used throughout
the repo-minify package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple, Optional, Union, Final, Literal

# Type aliases for graph operations
NodeID = str
NodeData = Dict[str, str]
EdgeData = Dict[str, str]
GraphData = Dict[str, List[Dict[str, str]]]

# Type aliases for dependency management
CommandResult = Tuple[bool, str]
ProcessOutput = Union[str, bytes]
VersionInfo = Dict[str, str]

# Type alias for logging levels
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Performance tracking type
Stats = Dict[str, Any]


@dataclass
class FileEntry:
    """Container for file content and metadata.

    Attributes:
        path: Relative path to the file
        content: File content as string

    Raises:
        ValueError: If path or content is empty

    Examples::
        >>> entry = FileEntry("test.py", "print('hello')")
        >>> entry.line_count
        1
        >>> entry.size
        13
    """

    path: str
    content: str

    def __post_init__(self) -> None:
        """Validate file entry attributes.

        Raises:
            ValueError: If path or content is empty
        """
        if not self.path.strip():
            raise ValueError("File path cannot be empty")
        if not self.content:
            raise ValueError("File content cannot be empty")

    @property
    def line_count(self) -> int:
        """Get the number of lines in the file.

        Returns:
            Number of lines in the file content

        Examples::
            >>> entry = FileEntry("test.py", "line1\\nline2")
            >>> entry.line_count
            2
        """
        return len(self.content.split("\n"))

    @property
    def size(self) -> int:
        """Get the file size in bytes.

        Returns:
            Size of file content in bytes

        Examples::
            >>> entry = FileEntry("test.py", "hello")
            >>> entry.size
            5
        """
        return len(self.content.encode("utf-8"))

    def __str__(self) -> str:
        """Get a string representation of the file entry.

        Returns:
            Formatted string with file info

        Examples::
            >>> str(FileEntry("test.py", "hello"))
            'test.py (1 lines, 5 bytes)'
        """
        return f"{self.path} ({self.line_count} lines, {self.size} bytes)"


@dataclass
class FileStats:
    """Statistics for a file or collection of files.

    Attributes:
        total_files: Number of files analyzed
        total_chars: Total character count (excluding whitespace)
        total_tokens: Total token count (words and symbols)
        file_path: Path to the analyzed file
        has_suspicious_files: Whether suspicious patterns were detected

    Raises:
        ValueError: If any numeric values are negative

    Examples::
        >>> stats = FileStats(1, 100, 20, "output.txt")
        >>> str(stats)
        '📊 File Stats:\\n────────────────\\n  Total Files: 1\\n  Total Chars: 100\\n Total Tokens: 20\\n       Output: output.txt\\n'
    """

    total_files: int
    total_chars: int
    total_tokens: int
    file_path: str
    has_suspicious_files: bool = False

    def __post_init__(self) -> None:
        """Validate statistics values.

        Raises:
            ValueError: If any numeric values are negative
        """
        if self.total_files < 0:
            raise ValueError("Total files cannot be negative")
        if self.total_chars < 0:
            raise ValueError("Total characters cannot be negative")
        if self.total_tokens < 0:
            raise ValueError("Total tokens cannot be negative")

    def __str__(self) -> str:
        """Format statistics for display.

        Returns:
            Formatted string with emoji and alignment

        Examples::
            >>> print(FileStats(1, 100, 20, "test.txt"))
            📊 File Stats:
            ────────────────
              Total Files: 1
              Total Chars: 100
             Total Tokens: 20
                   Output: test.txt
        """
        return (
            f"📊 File Stats:\n"
            f"────────────────\n"
            f"  Total Files: {self.total_files}\n"
            f"  Total Chars: {self.total_chars:,}\n"
            f" Total Tokens: {self.total_tokens:,}\n"
            f"       Output: {Path(self.file_path).name}\n"
        )


@dataclass
class DependencyVersion:
    """Container for dependency version information.

    Attributes:
        name: Name of the dependency
        version: Version string
        is_installed: Whether the dependency is installed
        install_time: Installation timestamp (if installed)
        install_path: Installation path (if installed)

    Raises:
        ValueError: If version string is empty or invalid

    Examples::
        >>> dep = DependencyVersion("python", "3.9.0")
        >>> str(dep)
        'python 3.9.0'
    """

    name: str
    version: str
    is_installed: bool = False
    install_time: Optional[float] = field(default=None)
    install_path: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        """Validate version string format.

        Raises:
            ValueError: If version string is empty
        """
        if not self.version.strip():
            raise ValueError("Version string cannot be empty")

    def __str__(self) -> str:
        """Format dependency version for display.

        Returns:
            Formatted string with name and version

        Examples::
            >>> str(DependencyVersion("node", "14.0.0"))
            'node 14.0.0'
        """
        return f"{self.name} {self.version}"
