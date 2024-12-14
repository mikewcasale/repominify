"""Graph export functionality for repo-minify.

This module handles exporting graph data to various file formats.

Performance Considerations:
    - File I/O is buffered for efficiency
    - Large graphs are written in chunks
    - Memory usage scales with graph size
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import networkx as nx
import yaml

from ..utils.logging import get_logger
from ..core.types import GraphData

logger = get_logger(__name__)


class GraphExporter:
    """Exports graph data to various file formats.

    This class handles saving graph data in multiple formats for different
    use cases (visualization, analysis, etc.).

    Attributes:
        stats: Runtime statistics for performance monitoring
    """

    def __init__(self) -> None:
        """Initialize exporter with performance tracking."""
        self.stats = {"files_written": 0, "total_bytes": 0, "export_time_ms": 0}

    def export_graph(
        self, graph: nx.DiGraph, output_dir: str, node_types: Dict[str, str]
    ) -> None:
        """Export graph to multiple formats.

        Args:
            graph: NetworkX graph to export
            output_dir: Directory to save output files
            node_types: Mapping of node types to colors

        Raises:
            OSError: If directory creation or file writing fails
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save as GraphML
        logger.debug("Exporting GraphML format...")
        graphml_path = output_path / "code_graph.graphml"
        nx.write_graphml(graph, graphml_path)
        self._update_stats(graphml_path)

        # Save as JSON for visualization
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

        # Save statistics
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

        logger.info(f"Graph exported to {output_dir}/")

    def _update_stats(self, file_path: Path) -> None:
        """Update export statistics.

        Args:
            file_path: Path to exported file
        """
        self.stats["files_written"] += 1
        self.stats["total_bytes"] += file_path.stat().st_size
