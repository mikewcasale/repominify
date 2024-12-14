"""Statistics and comparison functionality for repo-minify.

This module provides utilities for analyzing and comparing file sizes and content.

Author: Mike Casale
Email: mike@casale.xyz
GitHub: https://github.com/mikewcasale

Performance Considerations:
    - Memory: O(N) where N is file size
    - I/O: One read operation per file
    - CPU: Linear scan for pattern matching

Error Handling:
    - FileNotFoundError: When input files don't exist
    - UnicodeDecodeError: When files have invalid encoding
    - PermissionError: When files can't be accessed

Version Compatibility:
    - Python 3.7+: Full support
    - Type hints: Required for static analysis
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Final

# Security patterns to detect
SUSPICIOUS_PATTERNS: Final[Set[str]] = {
    'password', 'secret', 'token', 'api_key', 'private_key',
    'ssh_key', 'credentials', 'auth'
}

@dataclass
class FileStats:
    """Statistics for a file or collection of files.
    
    Attributes:
        total_files: Number of files analyzed
        total_chars: Total character count (excluding whitespace)
        total_tokens: Total token count (words and symbols)
        file_path: Path to the analyzed file
        has_suspicious_files: Whether suspicious patterns were detected
        
    Example:
        >>> stats = FileStats(total_files=1, total_chars=1000,
        ...                  total_tokens=200, file_path="example.txt")
        >>> print(stats)
        📊 File Stats:
        ────────────────
          Total Files: 1
          Total Chars: 1,000
         Total Tokens: 200
               Output: example.txt
             Security: ✔ No suspicious files detected
    """
    # Required fields
    total_files: int
    total_chars: int
    total_tokens: int
    file_path: str
    
    # Optional fields with defaults
    has_suspicious_files: bool = False

    def __str__(self) -> str:
        """Format statistics for display.
        
        Returns:
            Formatted string with emoji and alignment
            
        Performance:
            - Time: O(1) - Fixed string operations
            - Memory: O(1) - Fixed size output
        """
        return (
            f"📊 File Stats:\n"
            f"────────────────\n"
            f"  Total Files: {self.total_files}\n"
            f"  Total Chars: {self.total_chars:,}\n"
            f" Total Tokens: {self.total_tokens:,}\n"
            f"       Output: {Path(self.file_path).name}\n"
            f"     Security: {'❌ Suspicious files detected' if self.has_suspicious_files else '✔ No suspicious files detected'}\n"
        )

def analyze_file(file_path: str | Path) -> FileStats:
    """Analyze a file and generate statistics.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        FileStats object containing the analysis results
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be read
        UnicodeDecodeError: If the file has invalid encoding
        
    Example:
        >>> stats = analyze_file("repomix-output.txt")
        >>> print(f"Found {stats.total_files} files")
        Found 18 files
        
    Performance:
        - Time: O(N) where N is file size
        - Memory: O(N) for file content
        - I/O: One read operation
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            f"File {file_path} has invalid encoding. Please ensure it's UTF-8: {e}"
        )
    except PermissionError as e:
        raise PermissionError(
            f"Cannot read file {file_path}. Please check permissions: {e}"
        )
    
    # Count files by looking for "File: " markers
    total_files = content.count("File: ")
    
    # Get total characters (excluding whitespace)
    total_chars = len(''.join(content.split()))
    
    # Estimate tokens (words and symbols)
    total_tokens = len([t for t in content.split() if t.strip()])
    
    # Check for suspicious patterns
    has_suspicious = any(pattern in content.lower() 
                        for pattern in SUSPICIOUS_PATTERNS)
    
    return FileStats(
        total_files=total_files,
        total_chars=total_chars,
        total_tokens=total_tokens,
        file_path=str(file_path),
        has_suspicious_files=has_suspicious
    )

def compare_files(original_stats: FileStats, minified_stats: FileStats) -> str:
    """Generate a comparison report between original and minified files.
    
    Args:
        original_stats: Statistics for the original file
        minified_stats: Statistics for the minified file
        
    Returns:
        Formatted string containing the comparison
        
    Example:
        >>> original = FileStats(1, 1000, 200, "original.txt")
        >>> minified = FileStats(1, 500, 100, "minified.txt")
        >>> print(compare_files(original, minified))
        ... # Shows comparison with 50% reduction
    
    Performance:
        - Time: O(1) - Simple arithmetic operations
        - Memory: O(1) - Fixed size string output
        
    Note:
        The comparison assumes both files contain valid data and
        the minified file is derived from the original.
    """
    # Calculate reductions
    char_reduction = (
        (original_stats.total_chars - minified_stats.total_chars)
        / original_stats.total_chars * 100
    )
    token_reduction = (
        (original_stats.total_tokens - minified_stats.total_tokens)
        / original_stats.total_tokens * 100
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
        f"Security Notes: {'⚠️  Review recommended' if original_stats.has_suspicious_files else '✔ No issues found'}\n"
    )
