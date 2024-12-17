"""Text formatting functionality for repo-minify.

This module handles generating human-readable text representations of code graphs.
"""

from __future__ import annotations

from typing import Dict, List, Any

import networkx as nx

from .logging import get_logger

__all__ = ["GraphFormatter"]

logger = get_logger(__name__)


class GraphFormatter:
    """Formats graph data into human-readable text.

    This class provides functionality to generate text representations of
    code graphs for documentation and analysis.

    Attributes:
        stats: Dictionary tracking number of nodes processed and output size
    """

    __constants__ = []  # No constants defined for this class

    # Type hints for instance attributes
    stats: Dict[str, Any]

    def __init__(self) -> None:
        """Initialize formatter with statistics tracking.

        Examples::
            >>> formatter = GraphFormatter()
            >>> formatter.stats["nodes_processed"]
            0
        """
        self.stats = {"nodes_processed": 0, "total_chars": 0, "format_time_ms": 0}

    def generate_text_representation(
        self, graph: nx.DiGraph, node_types: Dict[str, str]
    ) -> str:
        """Generate a comprehensive text representation of the codebase.

        Args:
            graph (nx.DiGraph): NetworkX graph to format
            node_types (Dict[str, str]): Mapping of node types to colors

        Returns:
            str: Formatted string containing graph analysis and statistics

        Raises:
            KeyError: If required node attributes are missing
            ValueError: If graph is empty or malformed

        Examples::
            >>> formatter = GraphFormatter()
            >>> text = formatter.generate_text_representation(graph, node_types)
            >>> print(text.split("\\n")[0])
            # Code Graph Overview

        Notes:
            The output is organized into sections: overview, modules, and environment
            variables if present.
        """
        if not graph:
            raise ValueError("Cannot generate representation of empty graph")

        text_parts = self._generate_overview(graph, node_types)
        text_parts.extend(self._generate_module_structure(graph))
        text_parts.extend(self._generate_env_vars(graph))

        result = "\n".join(text_parts)
        self.stats["total_chars"] = len(result)
        return result

    def _generate_overview(
        self, graph: nx.DiGraph, node_types: Dict[str, str]
    ) -> List[str]:
        """Generate the overview section including node counts and type distribution.

        Args:
            graph (nx.DiGraph): NetworkX graph to format
            node_types (Dict[str, str]): Mapping of node types to colors

        Returns:
            List[str]: Lines of text for the overview section

        Raises:
            KeyError: If node type information is missing
        """
        text_parts = [
            "# Code Graph Overview",
            f"Total nodes: {graph.number_of_nodes()}",
            f"Total edges: {graph.number_of_edges()}\n",
            "## Node Type Distribution",
        ]

        for node_type in sorted(node_types):
            count = len(
                [n for n, d in graph.nodes(data=True) if d.get("type") == node_type]
            )
            text_parts.append(f"- {node_type}: {count}")
            self.stats["nodes_processed"] += count

        text_parts.extend(("", "## Module Structure"))
        return text_parts

    def _generate_module_structure(self, graph: nx.DiGraph) -> List[str]:
        """Generate the module structure section including imports, constants, classes, and functions.

        Args:
            graph (nx.DiGraph): NetworkX graph to format

        Returns:
            List[str]: Lines of text for the module structure section

        Raises:
            KeyError: If required node attributes are missing
        """
        text_parts = []
        for node, data in sorted(graph.nodes(data=True)):
            if data.get("type") != "module":
                continue

            text_parts.extend(self._format_module_header(node, data))
            text_parts.extend(self._format_module_imports(graph, node))
            text_parts.extend(self._format_module_constants(graph, node))
            text_parts.extend(self._format_module_classes(graph, node))
            text_parts.extend(self._format_module_functions(graph, node))

        return text_parts

    def _format_module_header(self, node: str, data: Dict) -> List[str]:
        """Format the module header section.

        Args:
            node (str): Name of the module
            data (Dict): Module metadata

        Returns:
            List[str]: Lines of text for the module header

        Raises:
            KeyError: If required metadata is missing
        """
        parts = [f"\n### Module: {node}"]
        if "path" in data:
            parts.append(f"Path: {data['path']}")
        return parts

    def _format_module_imports(self, graph: nx.DiGraph, module: str) -> List[str]:
        """Format the module imports section.

        Args:
            graph (nx.DiGraph): NetworkX graph to format
            module (str): Name of the module

        Returns:
            List[str]: Lines of text for the imports section

        Raises:
            KeyError: If required node attributes are missing
        """
        imports = self._get_neighbors_by_type(graph, module, "import")
        if not imports:
            return []

        return ["\nImports:"] + [f"- {imp}" for imp in sorted(imports)]

    def _format_module_constants(self, graph: nx.DiGraph, module: str) -> List[str]:
        """Format the module constants section.

        Args:
            graph (nx.DiGraph): NetworkX graph to format
            module (str): Name of the module

        Returns:
            List[str]: Lines of text for the constants section

        Raises:
            KeyError: If required node attributes are missing
        """
        constants = self._get_neighbors_by_type(graph, module, "constant")
        if not constants:
            return []

        parts = ["\nConstants:"]
        for const in sorted(constants):
            const_data = graph.nodes[const]
            parts.append(f"- {const.split('.')[-1]}: {const_data.get('value', '')}")
        return parts

    def _format_module_classes(self, graph: nx.DiGraph, module: str) -> List[str]:
        """Format the module classes section.

        Args:
            graph (nx.DiGraph): NetworkX graph to format
            module (str): Name of the module

        Returns:
            List[str]: Lines of text for the classes section

        Raises:
            KeyError: If required node attributes are missing
        """
        classes = self._get_neighbors_by_type(graph, module, "class")
        if not classes:
            return []

        parts = ["\nClasses:"]
        for class_name in sorted(classes):
            parts.extend(self._format_code_item(graph.nodes[class_name], class_name))
        return parts

    def _format_module_functions(self, graph: nx.DiGraph, module: str) -> List[str]:
        """Format the module functions section.

        Args:
            graph (nx.DiGraph): NetworkX graph to format
            module (str): Name of the module

        Returns:
            List[str]: Lines of text for the functions section

        Raises:
            KeyError: If required node attributes are missing
        """
        functions = self._get_neighbors_by_type(graph, module, "function")
        if not functions:
            return []

        parts = ["\nFunctions:"]
        for func_name in sorted(functions):
            parts.extend(self._format_code_item(graph.nodes[func_name], func_name))
        return parts

    def _get_neighbors_by_type(
        self, graph: nx.DiGraph, node: str, node_type: str
    ) -> List[str]:
        """Get all neighbors of a node with a specific type.

        Args:
            graph (nx.DiGraph): NetworkX graph to query
            node (str): Source node name
            node_type (str): Type of neighbors to find

        Returns:
            List[str]: Names of neighboring nodes of the specified type

        Raises:
            KeyError: If node type information is missing
        """
        return [
            n for n in graph.neighbors(node) if graph.nodes[n].get("type") == node_type
        ]

    def _format_code_item(self, item_data: Dict, item_name: str) -> List[str]:
        """Format a code item (class or function) with its signature and docstring.

        Args:
            item_data (Dict): Item metadata including signature and docstring
            item_name (str): Name of the code item

        Returns:
            List[str]: Lines of text for the code item

        Raises:
            KeyError: If required metadata is missing
        """
        parts = [f"\n{item_data.get('signature', item_name.split('.')[-1])}"]
        if "docstring" in item_data:
            parts.append(f"'''\n{item_data['docstring']}\n'''")
        return parts

    def _generate_env_vars(self, graph: nx.DiGraph) -> List[str]:
        """Generate the environment variables section.

        Args:
            graph (nx.DiGraph): NetworkX graph to format

        Returns:
            List[str]: Lines of text for the environment variables section

        Raises:
            KeyError: If required node attributes are missing
        """
        env_vars = [n for n, d in graph.nodes(data=True) if d.get("type") == "env_var"]
        if not env_vars:
            return []

        parts = ["\n## Environment Variables"]
        for var in sorted(env_vars):
            var_data = graph.nodes[var]
            parts.append(f"- {var.split('.')[-1]}: {var_data.get('value', '')}")
        return parts
