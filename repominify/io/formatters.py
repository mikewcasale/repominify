"""Text formatting functionality for repo-minify.

This module handles generating human-readable text representations of code graphs.

Performance Considerations:
    - Memory usage is O(N) where N is number of nodes
    - String operations are optimized for large graphs
"""

from __future__ import annotations

from typing import Dict, List

import networkx as nx

from ..utils.logging import get_logger

logger = get_logger(__name__)


class GraphFormatter:
    """Formats graph data into human-readable text.

    This class provides functionality to generate text representations of
    code graphs for documentation and analysis.

    Attributes:
        stats: Runtime statistics for performance monitoring
    """

    def __init__(self) -> None:
        """Initialize formatter with performance tracking."""
        self.stats = {"nodes_processed": 0, "total_chars": 0, "format_time_ms": 0}

    def generate_text_representation(
        self, graph: nx.DiGraph, node_types: Dict[str, str]
    ) -> str:
        """Generate a comprehensive text representation of the codebase.

        Args:
            graph: NetworkX graph to format
            node_types: Mapping of node types to colors

        Returns:
            Formatted string containing graph analysis and statistics

        Performance:
            - Memory usage scales with graph size
            - String concatenation is optimized
        """
        text_parts: List[str] = []

        # Add graph overview
        text_parts.append("# Code Graph Overview")
        text_parts.append(f"Total nodes: {graph.number_of_nodes()}")
        text_parts.append(f"Total edges: {graph.number_of_edges()}\n")

        # Add node type statistics
        text_parts.append("## Node Type Distribution")
        for node_type in sorted(node_types):
            count = len(
                [n for n, d in graph.nodes(data=True) if d.get("type") == node_type]
            )
            text_parts.append(f"- {node_type}: {count}")
            self.stats["nodes_processed"] += count
        text_parts.append("")

        # Add module information
        text_parts.append("## Module Structure")
        for node, data in sorted(graph.nodes(data=True)):
            if data.get("type") == "module":
                text_parts.append(f"\n### Module: {node}")
                if "path" in data:
                    text_parts.append(f"Path: {data['path']}")

                # List imports
                imports = [
                    n
                    for n in graph.neighbors(node)
                    if graph.nodes[n].get("type") == "import"
                ]
                if imports:
                    text_parts.append("\nImports:")
                    for imp in sorted(imports):
                        text_parts.append(f"- {imp}")

                # List constants
                constants = [
                    n
                    for n in graph.neighbors(node)
                    if graph.nodes[n].get("type") == "constant"
                ]
                if constants:
                    text_parts.append("\nConstants:")
                    for const in sorted(constants):
                        const_data = graph.nodes[const]
                        text_parts.append(
                            f"- {const.split('.')[-1]}: {const_data.get('value', '')}"
                        )

                # List classes with signatures and docstrings
                classes = [
                    n
                    for n in graph.neighbors(node)
                    if graph.nodes[n].get("type") == "class"
                ]
                if classes:
                    text_parts.append("\nClasses:")
                    for class_name in sorted(classes):
                        class_data = graph.nodes[class_name]
                        text_parts.append(
                            f"\n{class_data.get('signature', class_name.split('.')[-1])}"
                        )
                        if "docstring" in class_data:
                            text_parts.append(f"'''\n{class_data['docstring']}\n'''")

                # List functions with signatures and docstrings
                functions = [
                    n
                    for n in graph.neighbors(node)
                    if graph.nodes[n].get("type") == "function"
                ]
                if functions:
                    text_parts.append("\nFunctions:")
                    for func_name in sorted(functions):
                        func_data = graph.nodes[func_name]
                        text_parts.append(
                            f"\n{func_data.get('signature', func_name.split('.')[-1])}"
                        )
                        if "docstring" in func_data:
                            text_parts.append(f"'''\n{func_data['docstring']}\n'''")

        # Add environment variables if present
        env_vars = [n for n, d in graph.nodes(data=True) if d.get("type") == "env_var"]
        if env_vars:
            text_parts.append("\n## Environment Variables")
            for var in sorted(env_vars):
                var_data = graph.nodes[var]
                text_parts.append(
                    f"- {var.split('.')[-1]}: {var_data.get('value', '')}"
                )

        result = "\n".join(text_parts)
        self.stats["total_chars"] = len(result)
        return result
