"""Core graph building functionality for repo-minify.

This module provides the main graph building and analysis functionality.

Author: Mike Casale
Email: mike@casale.xyz
GitHub: https://github.com/mikewcasale

Performance Considerations:
    - Memory: O(N) where N is the total number of code entities
    - Time: O(M*L) where M is number of files and L is average lines per file
    - Graph operations are optimized for large codebases

Version Compatibility:
    - Python 3.7+: Full support
    - NetworkX 2.6+: Required for graph operations
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Final, Set

import networkx as nx

from ..utils.logging import get_logger
from ..utils.stats import FileStats, analyze_file, compare_files
from .parser import RepomixParser
from .types import FileEntry, GraphBuildError, ValidationError
from ..io.exporters import GraphExporter
from ..io.formatters import GraphFormatter

# Configure logging
logger = get_logger(__name__)

# Node type constants
NODE_TYPES: Final[Dict[str, str]] = {
    "module": "#A5D6A7",  # Light green
    "class": "#90CAF9",  # Light blue
    "function": "#FFCC80",  # Light orange
    "import": "#CE93D8",  # Light purple
    "constant": "#FFB74D",  # Orange
    "env_var": "#81C784",  # Green
}

# Patterns for finding constants
CONSTANT_PATTERNS: Final[List[str]] = [
    r"^[A-Z][A-Z0-9_]*$",  # All caps with underscores
    r"__[a-zA-Z0-9_]+__",  # Dunder names
    r"Final\[[^]]+\]",  # Type hints with Final
]


class CodeGraphBuilder:
    """Builds and analyzes code dependency graphs from Repomix output.

    This class provides functionality to parse Repomix output files and generate
    various representations of code structure and dependencies.

    Attributes:
        graph: A directed graph representing code dependencies
        node_types: Mapping of node types to their display colors
        stats: Runtime statistics for performance monitoring

    Performance:
        - Memory usage scales linearly with codebase size
        - Graph operations are O(N) for N nodes
        - File I/O is buffered for efficiency

    Thread Safety:
        This class is not thread-safe. Each instance should be used by a single thread.
    """

    __constants__ = [
        "NODE_TYPE_MODULE",
        "NODE_TYPE_CLASS",
        "NODE_TYPE_FUNCTION",
        "NODE_TYPE_IMPORT",
        "NODE_TYPE_CONSTANT",
        "NODE_TYPE_ENV_VAR",
    ]

    # Node type constants
    NODE_TYPE_MODULE: str = "module"
    NODE_TYPE_CLASS: str = "class"
    NODE_TYPE_FUNCTION: str = "function"
    NODE_TYPE_IMPORT: str = "import"
    NODE_TYPE_CONSTANT: str = "constant"
    NODE_TYPE_ENV_VAR: str = "env_var"

    # Type hints for instance attributes
    graph: nx.DiGraph
    node_types: Dict[str, str]
    stats: Dict[str, float]
    debug: bool
    parser: RepomixParser
    exporter: GraphExporter
    formatter: GraphFormatter

    def __init__(self, debug: bool = False) -> None:
        """Initialize a new CodeGraphBuilder instance.

        Args:
            debug: Enable debug logging and performance tracking

        Raises:
            ImportError: If required dependencies are not available
        """
        # Validate dependencies
        if not hasattr(nx, "write_graphml"):
            raise ImportError("NetworkX version >= 2.6 is required")

        # Initialize components
        self.parser = RepomixParser()
        self.exporter = GraphExporter()
        self.formatter = GraphFormatter()

        # Initialize graph
        self.graph = nx.DiGraph()
        self.node_types = NODE_TYPES

        # Performance tracking
        self.stats = {
            "total_time_ms": 0.0,
            "parse_time_ms": 0.0,
            "build_time_ms": 0.0,
            "export_time_ms": 0.0,
        }

        # Configure logging
        self.debug = debug
        if debug:
            logger.setLevel("DEBUG")

    def build_graph(self, file_entries: List[FileEntry]) -> nx.DiGraph:
        """Build a knowledge graph from the code analysis.

        Args:
            file_entries: List of FileEntry objects to analyze

        Returns:
            NetworkX DiGraph representing the code structure

        Raises:
            ValidationError: If input validation fails
            GraphBuildError: If graph construction fails

        Performance:
            - Time: O(M*L) where M is number of files and L is lines per file
            - Memory: O(N) where N is total number of code entities
        """
        if not file_entries:
            raise ValidationError("No file entries provided")

        start_time = time.time()
        logger.debug("Building graph from file entries...")

        try:
            # First add all files as module nodes, regardless of dependencies
            for entry in file_entries:
                self._add_module_node(entry)

            # Then add dependencies and constants for files that have them
            for entry in file_entries:
                self._add_import_nodes(entry)
                self._add_class_and_function_nodes(entry)
                self._add_constant_nodes(entry)

            # Add environment variables if .env file exists
            env_file = next((e for e in file_entries if e.path.endswith(".env")), None)
            if env_file:
                self._add_env_var_nodes(env_file)

        except Exception as e:
            raise GraphBuildError(f"Failed to build graph: {str(e)}")

        build_time = (time.time() - start_time) * 1000
        self.stats["build_time_ms"] = build_time
        logger.debug(f"Graph built in {build_time:.2f}ms")

        return self.graph

    def _add_module_node(self, entry: FileEntry) -> None:
        """Add a module node to the graph.

        Args:
            entry: FileEntry containing module information
        """
        module_name = Path(entry.path).stem
        self.graph.add_node(
            module_name,
            type=self.NODE_TYPE_MODULE,
            path=entry.path,
            color=self.node_types[self.NODE_TYPE_MODULE],
        )

    def _add_import_nodes(self, entry: FileEntry) -> None:
        """Add import nodes and relationships to the graph.

        Args:
            entry: FileEntry containing import information
        """
        module_name = Path(entry.path).stem
        imports = self.parser.analyze_imports(entry.content)
        for imp in imports:
            if not self.graph.has_node(imp):
                self.graph.add_node(
                    imp,
                    type=self.NODE_TYPE_IMPORT,
                    color=self.node_types[self.NODE_TYPE_IMPORT],
                )
            self.graph.add_edge(module_name, imp, relationship="imports")

    def _add_class_and_function_nodes(self, entry: FileEntry) -> None:
        """Add class and function nodes to the graph.

        Args:
            entry: FileEntry containing class and function information
        """
        module_name = Path(entry.path).stem
        content_lines = entry.content.split("\n")

        # Track current class/function and its docstring
        current_block = None
        current_signature = None
        current_docstring = []
        in_docstring = False

        for i, line in enumerate(content_lines):
            stripped = line.strip()

            # Handle docstring collection
            if in_docstring:
                if stripped.endswith('"""') or stripped.endswith("'''"):
                    current_docstring.append(stripped.rstrip("'\""))
                    in_docstring = False

                    # Add collected docstring to current node
                    if current_block and current_signature:
                        node_id = f"{module_name}.{current_block}"
                        self.graph.nodes[node_id]["docstring"] = "\n".join(
                            current_docstring
                        )
                        current_docstring = []
                else:
                    current_docstring.append(stripped)
                continue

            # Look for class definitions
            if stripped.startswith("class "):
                current_block = stripped[6:].split("(")[0].split(":")[0].strip()
                current_signature = stripped

                # Add class node with signature
                full_class_name = f"{module_name}.{current_block}"
                self.graph.add_node(
                    full_class_name,
                    type=self.NODE_TYPE_CLASS,
                    color=self.node_types[self.NODE_TYPE_CLASS],
                    signature=current_signature,
                )
                self.graph.add_edge(
                    module_name, full_class_name, relationship="contains"
                )

                # Check for docstring start
                if i + 1 < len(content_lines):
                    next_line = content_lines[i + 1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        in_docstring = True
                        current_docstring = [next_line.lstrip("'\"")]

            # Look for function definitions
            elif stripped.startswith("def "):
                # Capture multi-line function signature
                current_signature = stripped
                while not current_signature.endswith(":"):
                    i += 1
                    if i >= len(content_lines):
                        break
                    current_signature += " " + content_lines[i].strip()

                current_block = stripped[4:].split("(")[0].strip()

                # Add function node with signature
                full_func_name = f"{module_name}.{current_block}"
                self.graph.add_node(
                    full_func_name,
                    type=self.NODE_TYPE_FUNCTION,
                    color=self.node_types[self.NODE_TYPE_FUNCTION],
                    signature=current_signature,
                )
                self.graph.add_edge(
                    module_name, full_func_name, relationship="contains"
                )

                # Check for docstring start
                if i + 1 < len(content_lines):
                    next_line = content_lines[i + 1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        in_docstring = True
                        current_docstring = [next_line.lstrip("'\"")]

    def _add_constant_nodes(self, entry: FileEntry) -> None:
        """Add constant nodes to the graph.

        Args:
            entry: FileEntry containing constant definitions
        """
        module_name = Path(entry.path).stem
        constants: Set[str] = set()

        # Find constants using patterns
        for line in entry.content.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith(("#", "//", "/*", "*", '"', "'")):
                continue

            # Look for constant assignments
            if "=" in line:
                name = line.split("=")[0].strip()
                if name.isupper() and "_" in name:  # All caps with underscores
                    constants.add(name)
                elif name.startswith("__") and name.endswith("__"):  # Dunder names
                    constants.add(name)

            # Look for __constants__ list
            if line.startswith("__constants__"):
                try:
                    # Extract constants from list/tuple definition
                    const_list = line.split("=")[1].strip(" [](){}").replace("'", '"')
                    constants.update(
                        c.strip(" \"'") for c in const_list.split(",") if c.strip()
                    )
                except Exception:
                    pass

        # Add constant nodes
        for const in constants:
            const_id = f"{module_name}.{const}"
            self.graph.add_node(
                const_id,
                type=self.NODE_TYPE_CONSTANT,
                color=self.node_types[self.NODE_TYPE_CONSTANT],
                value=const,
            )
            self.graph.add_edge(module_name, const_id, relationship="defines")

    def _add_env_var_nodes(self, env_file: FileEntry) -> None:
        """Add environment variable nodes to the graph.

        Args:
            env_file: FileEntry containing environment variables
        """
        for line in env_file.content.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE format
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')

                # Add env var node
                self.graph.add_node(
                    f"env.{key}",
                    type=self.NODE_TYPE_ENV_VAR,
                    color=self.node_types[self.NODE_TYPE_ENV_VAR],
                    value=value,
                )

    def save_graph(
        self, output_dir: str, input_file: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Save the graph in multiple formats and generate comparison if input file provided.

        Args:
            output_dir: Directory to save output files
            input_file: Optional path to original Repomix output file for comparison

        Returns:
            Tuple of (text representation, comparison report if input file provided)

        Performance:
            - Time: O(N) where N is number of nodes
            - I/O: Multiple file write operations
        """
        start_time = time.time()

        # Export graph to files
        self.exporter.export_graph(self.graph, output_dir, self.node_types)

        # Generate and save text representation
        text_content = self.formatter.generate_text_representation(
            self.graph, self.node_types
        )

        text_path = Path(output_dir) / "code_graph.txt"
        with open(text_path, "w") as f:
            f.write(text_content)

        # Generate comparison if input file provided
        comparison_report = None
        if input_file:
            original_stats = analyze_file(input_file)
            minified_stats = analyze_file(str(text_path))
            comparison_report = compare_files(original_stats, minified_stats)

        export_time = (time.time() - start_time) * 1000
        self.stats["export_time_ms"] = export_time
        logger.debug(f"Graph exported in {export_time:.2f}ms")

        # Update total stats
        self.stats["total_time_ms"] = (
            self.stats["parse_time_ms"]
            + self.stats["build_time_ms"]
            + self.stats["export_time_ms"]
        )

        if self.debug:
            logger.debug("\nPerformance Statistics:")
            for key, value in self.stats.items():
                logger.debug(f"{key}: {value:.2f}ms")

        return text_content, comparison_report
