"""Command-line interface for repo-minify.

This module provides the main entry point for the repo-minify command-line tool.

Author: Mike Casale
Email: mike@casale.xyz
GitHub: https://github.com/mikewcasale

Error Handling:
    - Dependency errors are reported with clear instructions
    - File access errors include path information
    - Graph building errors show detailed context
    - All errors are logged with debug info when --debug is enabled

Performance:
    - Memory usage scales with input file size
    - Progress feedback for long operations
    - Graceful handling of large files

Version Compatibility:
    - Python 3.7+: Full support
    - Type hints: Required for static analysis
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, Optional, Final

from .core.graph import CodeGraphBuilder
from .utils.logging import configure_logging, get_logger
from .utils.dependency_checker import ensure_dependencies
from .core.types import GraphBuildError, FileParseError, ValidationError

# Configure logging
logger = get_logger(__name__)

# Exit codes
EXIT_SUCCESS: Final[int] = 0
EXIT_GENERAL_ERROR: Final[int] = 1
EXIT_FILE_NOT_FOUND: Final[int] = 2
EXIT_PERMISSION_ERROR: Final[int] = 3
EXIT_PARSE_ERROR: Final[int] = 4
EXIT_GRAPH_ERROR: Final[int] = 5

@dataclass
class CliOptions:
    """Container for command-line options.
    
    Attributes:
        input_file: Path to the Repomix output file
        output_dir: Directory for analysis output files
        debug: Whether to enable debug logging
        
    Example:
        >>> opts = CliOptions(Path("input.txt"), Path("output"), debug=True)
        >>> print(opts.input_file)
        input.txt
    """
    # Required fields
    input_file: Path
    output_dir: Path
    
    # Optional fields with defaults
    debug: bool = False

def parse_args() -> CliOptions:
    """Parse command-line arguments.
    
    Returns:
        CliOptions containing validated arguments
        
    Example:
        >>> args = parse_args()
        >>> print(f"Processing {args.input_file}")
        Processing repomix-output.txt
        
    Note:
        Uses argparse's built-in help and error handling
    """
    parser = argparse.ArgumentParser(
        description="Analyze and minify code repository structure using Repomix.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Basic usage
  repo-minify repomix-output.txt
  
  # Specify output directory
  repo-minify repomix-output.txt -o output_dir
  
  # Enable debug logging
  repo-minify repomix-output.txt --debug
        """
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the Repomix output file"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("repo_minify_output"),
        help="Output directory for analysis files"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    return CliOptions(
        input_file=args.input_file,
        output_dir=args.output_dir,
        debug=args.debug
    )

def handle_error(error: Exception, debug: bool) -> NoReturn:
    """Handle errors with appropriate messaging and logging.
    
    Args:
        error: The exception to handle
        debug: Whether debug mode is enabled
        
    Note:
        Always exits the program with an appropriate status code
        
    Exit Codes:
        1: General error
        2: File not found
        3: Permission denied
        4: Parse error
        5: Graph build error
    """
    if isinstance(error, FileNotFoundError):
        print(f"Error: File not found: {error.filename}", file=sys.stderr)
        sys.exit(EXIT_FILE_NOT_FOUND)
    elif isinstance(error, PermissionError):
        print(f"Error: Permission denied: {error.filename}", file=sys.stderr)
        sys.exit(EXIT_PERMISSION_ERROR)
    elif isinstance(error, (FileParseError, ValidationError)):
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(EXIT_PARSE_ERROR)
    elif isinstance(error, GraphBuildError):
        print(f"Error building graph: {error}", file=sys.stderr)
        sys.exit(EXIT_GRAPH_ERROR)
    else:
        print(f"Error: {error}", file=sys.stderr)
        if debug:
            raise
        sys.exit(EXIT_GENERAL_ERROR)

def main() -> int:
    """Main entry point for the repo-minify CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
        
    Exit Codes:
        0: Success
        1: General error
        2: File not found
        3: Permission denied
        4: Parse error
        5: Graph build error
        
    Example:
        >>> sys.exit(main())  # Run the CLI
    """
    try:
        # Parse arguments
        args = parse_args()
        
        # Configure logging
        configure_logging(debug=args.debug)
        
        # Check dependencies
        if not ensure_dependencies():
            print("Failed to verify required dependencies", file=sys.stderr)
            logger.debug("Dependency check failed")
            return EXIT_GENERAL_ERROR
        
        # Create output directory
        args.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create graph builder
        builder = CodeGraphBuilder(debug=args.debug)
        
        # Parse input file
        logger.info(f"Parsing {args.input_file}")
        file_entries = builder.parser.parse_file(str(args.input_file))
        print(f"Found {len(file_entries)} files to analyze")
        
        # Build graph
        logger.info("Building dependency graph")
        graph = builder.build_graph(file_entries)
        print(f"Built graph with {graph.number_of_nodes()} nodes")
        
        # Save outputs and get comparison
        logger.info(f"Saving outputs to {args.output_dir}")
        _, comparison = builder.save_graph(
            str(args.output_dir),
            input_file=str(args.input_file)
        )
        
        if comparison:
            print("\nAnalysis Complete!")
            print(comparison)
        
        print(f"\nOutput files saved to: {args.output_dir}/")
        return EXIT_SUCCESS
        
    except Exception as e:
        handle_error(e, args.debug if 'args' in locals() else False)

if __name__ == "__main__":
    sys.exit(main())