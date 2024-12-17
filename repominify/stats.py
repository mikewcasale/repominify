"""Statistics and comparison functionality for repo-minify.

This module provides utilities for analyzing and comparing file sizes and content.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union, Set

from .types import FileStats
from .constants import SUSPICIOUS_PATTERNS


def analyze_file(file_path: Union[str, Path]) -> FileStats:
    """Analyze a file and generate statistics.

    Args:
        file_path: Path to the file to analyze

    Returns:
        FileStats object containing the analysis results

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be read
        UnicodeDecodeError: If the file has invalid encoding

    Examples::
        >>> stats = analyze_file("repomix-output.txt")
        >>> print(f"Found {stats.total_files} files")
        Found 18 files
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            f"File {file_path} has invalid encoding. Please ensure it's UTF-8: {e}"
        ) from e
    except PermissionError as e:
        raise PermissionError(
            f"Cannot read file {file_path}. Please check permissions: {e}"
        ) from e

    total_files: int = 0
    file_path_str: str = str(file_path)

    # Count files based on the file type
    if file_path_str.endswith("code_graph.txt"):
        # For the output file, count module nodes from the Node Type Distribution section
        for line in content.splitlines():
            if line.strip().startswith("- module:"):
                try:
                    total_files = int(line.split(":")[1].strip())
                    break
                except (ValueError, IndexError):
                    total_files = 0
    else:
        # For input file, count unique "File: " entries
        unique_files: Set[str] = set()
        for line in content.splitlines():
            if line.strip().startswith("File: "):
                file_entry = line.strip()[6:].strip()  # Remove "File: " prefix
                unique_files.add(file_entry)
        total_files = len(unique_files)

    # Get total characters (excluding whitespace)
    total_chars: int = len("".join(content.split()))

    # Estimate tokens (words and symbols)
    total_tokens: int = len([t for t in content.split() if t.strip()])

    return FileStats(
        total_files=total_files,
        total_chars=total_chars,
        total_tokens=total_tokens,
        file_path=file_path_str,
        has_suspicious_files=False,  # No longer used in output
    )


def compare_files(original_stats: FileStats, minified_stats: FileStats) -> str:
    """Generate a comparison report between original and minified files.

    Args:
        original_stats: Statistics for the original file
        minified_stats: Statistics for the minified file

    Returns:
        Formatted string containing the comparison

    Raises:
        ZeroDivisionError: If original file has zero characters or tokens

    Examples::
        >>> original = FileStats(1, 1000, 200, "original.txt")
        >>> minified = FileStats(1, 500, 100, "minified.txt")
        >>> print(compare_files(original, minified))
        ... # Shows comparison with 50% reduction
    """
    # Calculate reductions
    char_reduction: float = (
        (original_stats.total_chars - minified_stats.total_chars)
        / original_stats.total_chars
        * 100
    )
    token_reduction: float = (
        (original_stats.total_tokens - minified_stats.total_tokens)
        / original_stats.total_tokens
        * 100
    )

    # Generate report
    return (
        f"{original_stats}\n"
        f"\n"
        f"{minified_stats}\n"
        f"\n"
        f"📈 Comparison:\n"
        f"────────────────\n"
        f" Char Reduction: {char_reduction:.1f}%\n"
        f"Token Reduction: {token_reduction:.1f}%\n"
    )
