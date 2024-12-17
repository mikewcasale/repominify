"""Graph export functionality for repo-minify.

This module handles exporting graph data to various file formats.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import networkx as nx
import yaml

from .logging import get_logger
from .types import GraphData

__all__ = ["GraphExporter"]

logger = get_logger(__name__)


class GraphExporter:
    """Exports graph data to various file formats.

    This class handles saving graph data in multiple formats for different
    use cases (visualization, analysis, etc.).

    Attributes:
        stats: Dictionary tracking export statistics (files written, bytes, time)
    """

    __constants__ = []  # No constants defined for this class

    # Type hints for instance attributes
    stats: Dict[str, int]

    def __init__(self) -> None:
        """Initialize exporter with statistics tracking.

        Examples::
            >>> exporter = GraphExporter()
            >>> exporter.stats["files_written"]
            0
        """
        self.stats = {"files_written": 0, "total_bytes": 0, "export_time_ms": 0}

    def export_graph(
        self, graph: nx.DiGraph, output_dir: str, node_types: Dict[str, str]
    ) -> None:
        """Export graph to multiple formats.

        Args:
            graph (nx.DiGraph): NetworkX graph to export
            output_dir (str): Directory to save output files
            node_types (Dict[str, str]): Mapping of node types to colors

        Raises:
            OSError: If directory creation or file writing fails
            ValueError: If graph is empty or node_types is empty

        Examples::
            >>> exporter = GraphExporter()
            >>> exporter.export_graph(graph, "output", {"module": "#000"})
            >>> Path("output/code_graph.graphml").exists()
            True

        Notes:
            Creates three files:
            - code_graph.graphml: GraphML format for visualization tools
            - code_graph.json: JSON format for web visualization
            - graph_statistics.yaml: YAML format for statistics
        """
        if not graph:
            raise ValueError("Cannot export empty graph")
        if not node_types:
            raise ValueError("Node types mapping cannot be empty")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self._export_graphml(graph, output_path)
        self._export_json(graph, output_path)
        self._export_statistics(graph, output_path, node_types)

        logger.info(f"Graph exported to {output_dir}/")

    def _export_graphml(self, graph: nx.DiGraph, output_path: Path) -> None:
        """Export graph in GraphML format.

        Args:
            graph (nx.DiGraph): NetworkX graph to export
            output_path (Path): Directory to save the file

        Raises:
            OSError: If file writing fails
        """
        logger.debug("Exporting GraphML format...")
        graphml_path = output_path / "code_graph.graphml"
        nx.write_graphml(graph, graphml_path)
        self._update_stats(graphml_path)

    def _export_json(self, graph: nx.DiGraph, output_path: Path) -> None:
        """Export graph in JSON format for visualization.

        Args:
            graph (nx.DiGraph): NetworkX graph to export
            output_path (Path): Directory to save the file

        Raises:
            OSError: If file writing fails
        """
        logger.debug("Exporting JSON format...")
        graph_data: GraphData = {
            "nodes": [
                {
                    "id": node,
                    "type": data.get("type", "unknown"),
                    "color": data.get("color", "#CCCCCC"),
                    "path": data.get("path", ""),
                }
                for node, data in graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "relationship": data.get("relationship", "unknown"),
                }
                for source, target, data in graph.edges(data=True)
            ],
        }

        json_path = output_path / "code_graph.json"
        with open(json_path, "w") as f:
            json.dump(graph_data, f, indent=2)
        self._update_stats(json_path)

    def _export_statistics(
        self, graph: nx.DiGraph, output_path: Path, node_types: Dict[str, str]
    ) -> None:
        """Export graph statistics in YAML format.

        Args:
            graph (nx.DiGraph): NetworkX graph to export
            output_path (Path): Directory to save the file
            node_types (Dict[str, str]): Mapping of node types to colors

        Raises:
            OSError: If file writing fails
        """
        logger.debug("Exporting statistics...")
        stats = {
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "node_types": {
                node_type: len(
                    [n for n, d in graph.nodes(data=True) if d.get("type") == node_type]
                )
                for node_type in node_types
            },
        }

        yaml_path = output_path / "graph_statistics.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(stats, f, default_flow_style=False)
        self._update_stats(yaml_path)

    def _update_stats(self, file_path: Path) -> None:
        """Update export statistics.

        Args:
            file_path (Path): Path to exported file

        Raises:
            OSError: If file size cannot be determined
        """
        self.stats["files_written"] += 1
        self.stats["total_bytes"] += file_path.stat().st_size
