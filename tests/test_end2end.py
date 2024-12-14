import os
import pytest
from pathlib import Path
from repominify import CodeGraphBuilder, ensure_dependencies, configure_logging


@pytest.fixture
def output_dir(tmp_path) -> Path:
    """Fixture to provide a temporary output directory."""
    return tmp_path / "output"


@pytest.fixture
def repomix_file() -> Path:
    """Fixture to provide the path to the test Repomix output file."""
    tests_dir = Path(__file__).parent
    return tests_dir / "data" / "repomix-output.txt"


def test_end_to_end(output_dir: Path, repomix_file: Path) -> None:
    """
    End-to-end test of the repo-minify package functionality.

    Tests the complete workflow:
    1. Dependency checking
    2. Repomix file parsing
    3. Graph building
    4. Output generation
    5. File comparison
    """
    # Configure logging
    configure_logging(debug=True)

    # Check dependencies
    assert ensure_dependencies(), "Failed to verify dependencies"

    # Create graph builder
    builder = CodeGraphBuilder(debug=True)

    # Ensure test file exists
    assert repomix_file.exists(), f"Test file not found: {repomix_file}"

    # Parse the Repomix output file
    file_entries = builder.parser.parse_file(str(repomix_file))
    assert len(file_entries) > 0, "No file entries found in Repomix output"

    # Build the graph
    graph = builder.build_graph(file_entries)
    assert graph.number_of_nodes() > 0, "Graph was built but contains no nodes"

    # Save outputs and get comparison
    output_dir.mkdir(exist_ok=True)
    text_content, comparison = builder.save_graph(
        str(output_dir), input_file=str(repomix_file)
    )

    # Verify outputs were created
    assert output_dir.exists(), "Output directory was not created"
    expected_files = {
        "code_graph.graphml",
        "code_graph.json",
        "graph_statistics.yaml",
        "code_graph.txt",
    }
    actual_files = {f.name for f in output_dir.iterdir()}
    assert expected_files.issubset(
        actual_files
    ), f"Missing expected output files. Found: {actual_files}"

    # Verify comparison was generated
    assert comparison is not None, "No comparison report generated"
    assert "📊 File Stats:" in comparison, "Missing file stats in comparison"
    assert "📈 Comparison:" in comparison, "Missing comparison section"
    assert "Char Reduction:" in comparison, "Missing character reduction stats"
    assert "Token Reduction:" in comparison, "Missing token reduction stats"

    # Print the comparison for visibility
    print("\nFile Comparison Report:")
    print("─" * 40)
    print(comparison)
