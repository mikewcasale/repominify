"""Constants used throughout the repo-minify package.

This module centralizes all constant values used across different modules.

Attributes:
    EXIT_SUCCESS: Exit code for successful execution (0)
    EXIT_GENERAL_ERROR: Exit code for general errors (1)
    EXIT_FILE_NOT_FOUND: Exit code for file not found errors (2)
    EXIT_PERMISSION_ERROR: Exit code for permission errors (3)
    EXIT_PARSE_ERROR: Exit code for parsing errors (4)
    EXIT_GRAPH_ERROR: Exit code for graph building errors (5)
    NODE_TYPES: Mapping of node types to their display colors
    CONSTANT_PATTERNS: Regular expressions for identifying constants
    SUSPICIOUS_PATTERNS: Set of security-sensitive pattern strings

Examples::
    >>> from repominify.constants import NODE_TYPES
    >>> NODE_TYPES["module"]
    '#A5D6A7'
"""

from __future__ import annotations

from typing import Dict, List, Set, Final

# Exit codes
EXIT_SUCCESS: Final[int] = 0
EXIT_GENERAL_ERROR: Final[int] = 1
EXIT_FILE_NOT_FOUND: Final[int] = 2
EXIT_PERMISSION_ERROR: Final[int] = 3
EXIT_PARSE_ERROR: Final[int] = 4
EXIT_GRAPH_ERROR: Final[int] = 5

# Node type constants with color codes
NODE_TYPES: Final[Dict[str, str]] = {
    "module": "#A5D6A7",  # Light green
    "class": "#90CAF9",  # Light blue
    "function": "#FFCC80",  # Light orange
    "import": "#CE93D8",  # Light purple
    "constant": "#FFB74D",  # Orange
    "env_var": "#81C784",  # Green
}

# Regular expression patterns for identifying constants
CONSTANT_PATTERNS: Final[List[str]] = [
    r"^[A-Z][A-Z0-9_]*$",  # All caps with underscores
    r"__[a-zA-Z0-9_]+__",  # Dunder names
    r"Final\[[^]]+\]",  # Type hints with Final
]

# Security-sensitive patterns to detect
SUSPICIOUS_PATTERNS: Final[Set[str]] = {
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "ssh_key",
    "credentials",
    "auth",
}
