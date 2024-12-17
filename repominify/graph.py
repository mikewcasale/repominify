"""Core graph building functionality for repo-minify.

This module provides the main graph building and analysis functionality.
"""

from __future__ import annotations

import contextlib
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

import networkx as nx

from .logging import get_logger
from .stats import FileStats, analyze_file, compare_files
from .parser import RepomixParser
from .types import FileEntry
from .exceptions import GraphBuildError, ValidationError
from .exporters import GraphExporter
from .formatters import GraphFormatter
from .constants import NODE_TYPES, CONSTANT_PATTERNS

__all__ = ["CodeGraphBuilder"]

# Configure logging
logger = get_logger(__name__)


class CodeGraphBuilder:
    """Builds and analyzes code dependency graphs from Repomix output.

    This class provides functionality to parse Repomix output files and generate
    various representations of code structure and dependencies.

    Attributes:
        graph: A directed graph representing code dependencies
        node_types: Mapping of node types to their display colors
        stats: Runtime statistics for performance monitoring
        debug: Whether debug logging is enabled
        parser: Parser for Repomix output
        exporter: Graph export functionality
        formatter: Text formatting functionality

    Notes:
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
            debug (bool): Enable debug logging and performance tracking

        Raises:
            ImportError: If required dependencies are not available

        Examples::
            >>> builder = CodeGraphBuilder(debug=True)
            >>> builder.debug
            True
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
            file_entries (List[FileEntry]): List of FileEntry objects to analyze

        Returns:
            nx.DiGraph: NetworkX DiGraph representing the code structure

        Raises:
            ValidationError: If input validation fails
            GraphBuildError: If graph construction fails

        Examples::
            >>> entries = [FileEntry("test.py", "def hello(): pass")]
            >>> graph = builder.build_graph(entries)
            >>> len(graph.nodes())
            1
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
            raise GraphBuildError(f"Failed to build graph: {str(e)}") from e

        self._update_stats(start_time, "build_time_ms", "Graph built in ")
        return self.graph

    def _add_module_node(self, entry: FileEntry) -> None:
        """Add a module node to the graph.

        Args:
            entry (FileEntry): FileEntry containing module information

        Examples::
            >>> entry = FileEntry("test.py", "")
            >>> builder._add_module_node(entry)
            >>> "test" in builder.graph.nodes()
            True
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
            entry (FileEntry): FileEntry containing import information

        Examples::
            >>> entry = FileEntry("test.py", "import os")
            >>> builder._add_import_nodes(entry)
            >>> "os" in builder.graph.nodes()
            True
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

    def _update_stats(self, start_time: float, stat_key: str, message: str) -> None:
        """Update timing statistics and log debug message.

        Args:
            start_time (float): Start time of the operation
            stat_key (str): Key to update in stats dictionary
            message (str): Message prefix for debug logging
        """
        elapsed = (time.time() - start_time) * 1000
        self.stats[stat_key] = elapsed
        logger.debug(f"{message}{elapsed:.2f}ms")

    def _add_class_and_function_nodes(self, entry: FileEntry) -> None:
        """Add class and function nodes to the graph.

        Args:
            entry (FileEntry): FileEntry containing class and function information

        Examples::
            >>> entry = FileEntry("test.py", "class Test: pass")
            >>> builder._add_class_and_function_nodes(entry)
            >>> "test.Test" in builder.graph.nodes()
            True
        """
        module_name = Path(entry.path).stem
        content_lines = entry.content.split("\n")

        for i, line in enumerate(content_lines):
            if not line.strip():
                continue

            if line.strip().startswith("class "):
                self._handle_class_definition(module_name, content_lines, i)
            elif line.strip().startswith("def "):
                self._handle_function_definition(module_name, content_lines, i)

    def _handle_class_definition(
        self, module_name: str, content_lines: List[str], line_idx: int
    ) -> None:
        """Handle a class definition and add it to the graph.

        Args:
            module_name (str): Name of the module containing the class
            content_lines (List[str]): Lines of code to process
            line_idx (int): Index of the class definition line

        Examples::
            >>> lines = ["class Test:", "    pass"]
            >>> builder._handle_class_definition("module", lines, 0)
            >>> "module.Test" in builder.graph.nodes()
            True
        """
        line = content_lines[line_idx].strip()
        class_name = line[6:].split("(")[0].split(":")[0].strip()
        full_class_name = f"{module_name}.{class_name}"

        self._add_node_with_signature(
            full_class_name, self.NODE_TYPE_CLASS, line, module_name
        )

        self._add_docstring_if_present(full_class_name, content_lines, line_idx)

    def _handle_function_definition(
        self, module_name: str, content_lines: List[str], line_idx: int
    ) -> None:
        """Handle a function definition and add it to the graph.

        Args:
            module_name (str): Name of the module containing the function
            content_lines (List[str]): Lines of code to process
            line_idx (int): Index of the function definition line

        Examples::
            >>> lines = ["def test():", "    pass"]
            >>> builder._handle_function_definition("module", lines, 0)
            >>> "module.test" in builder.graph.nodes()
            True
        """
        signature = self._get_full_signature(content_lines, line_idx)
        func_name = content_lines[line_idx].strip()[4:].split("(")[0].strip()
        full_func_name = f"{module_name}.{func_name}"

        self._add_node_with_signature(
            full_func_name, self.NODE_TYPE_FUNCTION, signature, module_name
        )

        self._add_docstring_if_present(full_func_name, content_lines, line_idx)

    def _get_full_signature(self, content_lines: List[str], start_idx: int) -> str:
        """Get the complete function signature, handling multi-line definitions.

        Args:
            content_lines (List[str]): Lines of code to process
            start_idx (int): Starting line index of the signature

        Returns:
            str: Complete function signature including all lines

        Examples::
            >>> lines = ["def test(", "        x: int", "    ):", "    pass"]
            >>> builder._get_full_signature(lines, 0)
            'def test( x: int ):'
        """
        signature = content_lines[start_idx].strip()
        current_idx = start_idx

        while not signature.endswith(":"):
            current_idx += 1
            if current_idx >= len(content_lines):
                break
            signature += f" {content_lines[current_idx].strip()}"

        return signature

    def _add_node_with_signature(
        self, node_id: str, node_type: str, signature: str, module_name: str
    ) -> None:
        """Add a node with its signature to the graph.

        Args:
            node_id (str): Unique identifier for the node
            node_type (str): Type of node (class or function)
            signature (str): Full signature of the code item
            module_name (str): Name of the containing module

        Examples::
            >>> builder._add_node_with_signature("mod.func", "function", "def func():", "mod")
            >>> "mod.func" in builder.graph.nodes()
            True
        """
        self.graph.add_node(
            node_id,
            type=node_type,
            color=self.node_types[node_type],
            signature=signature,
        )
        self.graph.add_edge(module_name, node_id, relationship="contains")

    def _add_docstring_if_present(
        self, node_id: str, content_lines: List[str], line_idx: int
    ) -> None:
        """Add docstring to a node if one follows the definition.

        Args:
            node_id (str): Identifier of the node to add docstring to
            content_lines (List[str]): Lines of code to process
            line_idx (int): Index of the definition line

        Examples::
            >>> lines = ["def test():", "    # docstring", "    pass"]
            >>> builder._add_docstring_if_present("mod.test", lines, 0)
            >>> "docstring" in builder.graph.nodes["mod.test"].get("docstring", "")
            True
        """
        if line_idx + 1 >= len(content_lines):
            return

        next_line = content_lines[line_idx + 1].strip()
        if not (next_line.startswith('"""') or next_line.startswith("'''")):
            return

        docstring = [next_line.lstrip("'\"")]
        for line in content_lines[line_idx + 2 :]:
            stripped = line.strip()
            if stripped.endswith('"""') or stripped.endswith("'''"):
                docstring.append(stripped.rstrip("'\""))
                break
            docstring.append(stripped)

        self.graph.nodes[node_id]["docstring"] = "\n".join(docstring)

    def _add_constant_nodes(self, entry: FileEntry) -> None:
        """Add constant nodes to the graph.

        Args:
            entry (FileEntry): FileEntry containing constant definitions

        Examples::
            >>> entry = FileEntry("test.py", "CONSTANT = 42")
            >>> builder._add_constant_nodes(entry)
            >>> "test.CONSTANT" in builder.graph.nodes()
            True
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
                with contextlib.suppress(Exception):
                    # Extract constants from list/tuple definition
                    const_list = line.split("=")[1].strip(" [](){}").replace("'", '"')
                    constants.update(
                        c.strip(" \"'") for c in const_list.split(",") if c.strip()
                    )

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
            env_file (FileEntry): FileEntry containing environment variables

        Examples::
            >>> env = FileEntry(".env", "API_KEY=secret")
            >>> builder._add_env_var_nodes(env)
            >>> "env.API_KEY" in builder.graph.nodes()
            True
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
            output_dir (str): Directory to save output files
            input_file (Optional[str]): Optional path to original Repomix output file for comparison

        Returns:
            Tuple[str, Optional[str]]: Tuple of (text representation, comparison report if input file provided)

        Examples::
            >>> text, report = builder.save_graph("output")
            >>> isinstance(text, str)
            True
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

        self._update_stats(start_time, "export_time_ms", "Graph exported in ")

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
