# repominify

A Python package that optimizes codebase representations for Large Language Models (LLMs) by generating compact, context-rich summaries that minimize token usage while preserving essential structural information.

[![PyPI version](https://badge.fury.io/py/repominify.svg)](https://badge.fury.io/py/repominify)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

repominify helps you provide detailed context about your codebase to LLMs without consuming excessive space in their context windows. It processes Repomix output to create optimized representations that maintain critical structural information while significantly reducing token usage. This enables more efficient and effective code-related conversations with AI models by maximizing the amount of useful context that can fit within token limits.

⚠️ Warning: repominify performs deep code analysis which can be resource-intensive for large codebases. Please start with a small subset of your code to understand the process and resource requirements.

## Features

- **Automatic Dependency Management**
  - Checks and installs Node.js and npm dependencies
  - Automatically installs Repomix if not present
  - Handles version compatibility checks

- **Code Analysis**
  - Parses and analyzes code structure
  - Extracts imports, classes, and functions
  - Builds dependency graphs
  - Performance optimized for large codebases

- **Multiple Output Formats**
  - GraphML for visualization tools
  - JSON for web-based tools
  - YAML for statistics
  - Text for human-readable analysis

- **Size Optimization**
  - Generates minified code structure representation
  - Provides detailed size reduction statistics
  - Shows character and token reduction percentages
  - Maintains semantic meaning while reducing size

- **Security Awareness**
  - Detects potentially sensitive patterns
  - Provides security recommendations
  - Flags suspicious file content
  - Helps maintain security best practices

- **Debug Support**
  - Comprehensive logging
  - Performance tracking
  - Detailed error messages

## Installation

```bash
pip install repominify
```

## Requirements

- Python 3.7 or higher
- Node.js 12+ (will be checked during runtime)
- npm 6+ (will be checked during runtime)
- Repomix (will be installed automatically if not present)

## Usage

### Command Line

```bash
# Basic usage
repominify path/to/repomix-output.txt

# Specify output directory
repominify path/to/repomix-output.txt -o output_dir

# Enable debug logging
repominify path/to/repomix-output.txt --debug
```

### Python API

```python
from repominify import CodeGraphBuilder, ensure_dependencies, configure_logging

# Enable debug logging (optional)
configure_logging(debug=True)

# Check dependencies
if ensure_dependencies():
    # Create graph builder
    builder = CodeGraphBuilder()
    
    # Parse the Repomix output file
    file_entries = builder.parser.parse_file("repomix-output.txt")
    
    # Build the graph
    graph = builder.build_graph(file_entries)
    
    # Save outputs and get comparison
    text_content, comparison = builder.save_graph(
        "output_directory",
        input_file="repomix-output.txt"
    )
    
    # Print comparison
    print(comparison)
```

### Example Output

```
Analysis Complete!
📊 File Stats:
────────────────
  Total Files: 18
  Total Chars: 1,091,801
 Total Tokens: 354,159
       Output: repomix-output.txt
     Security: ✔ No suspicious files detected

📊 File Stats:
────────────────
  Total Files: 18
  Total Chars: 245,123
 Total Tokens: 89,456
       Output: code_graph.txt
     Security: ✔ No suspicious files detected

📈 Comparison:
────────────────
 Char Reduction: 77.5%
Token Reduction: 74.7%
Security Notes: ✔ No issues found
```

## Project Structure

```
repominify/
├── src/                 # Source code
│   ├── core/           # Core functionality
│   │   ├── graph.py    # Graph building and analysis
│   │   ├── parser.py   # Repomix file parsing
│   │   └── types.py    # Shared types and data structures
│   ├── io/             # Input/Output operations
│   │   ├── exporters.py  # Graph export functionality
│   │   └── formatters.py # Text representation formatting
│   ├── utils/          # Utility modules
│   │   ├── dependency_checker.py  # Dependency management
│   │   ├── logging.py   # Logging configuration
│   │   └── stats.py     # Statistics and comparison
│   ├── cli.py          # Command-line interface
│   └── __init__.py     # Package initialization
├── tests/              # Test suite
│   ├── test_end2end.py  # End-to-end tests
│   └── data/          # Test data files
├── setup.py           # Package configuration
├── pyproject.toml     # Build system requirements
├── LICENSE            # MIT License
└── README.md          # This file
```

## Output Files

When you run repominify, it generates several files in your output directory:

- `code_graph.graphml`: Graph representation in GraphML format
- `code_graph.json`: Graph data in JSON format for web visualization
- `graph_statistics.yaml`: Statistical analysis of the codebase
- `code_graph.txt`: Human-readable text representation

## Performance

repominify is designed to handle large codebases efficiently:

- Memory usage scales linearly with codebase size
- File I/O is buffered for efficiency
- Graph operations are optimized
- Performance statistics available in debug mode

## Error Handling

The package provides detailed error messages and proper error boundaries:

- Dependency errors (Node.js, npm, Repomix)
- File parsing errors
- Graph building errors
- Export errors

## Development

To set up for development:

```bash
# Clone the repository
git clone https://github.com/mikewcasale/repominify.git
cd repominify

# Install in development mode with test dependencies
pip install -e '.[dev]'

# Run tests
pytest tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. By contributing to this project, you agree to abide by its terms.

This project has adopted the [Python Style Guide](STYLEGUIDE.md) for consistency and maintainability.

## Authors

**Mike Casale**
- Email: mike@casale.xyz
- GitHub: [@mikewcasale](https://github.com/mikewcasale)
- Website: [casale.xyz](https://casale.xyz)

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project makes use of or was influenced by several excellent open source projects:

- [Repomix](https://github.com/yamadashy/repomix) - Our analysis pipeline integrates with this Node.js tool for initial code scanning
- [NetworkX](https://networkx.org/) - Core graph algorithms and data structures
- [PyYAML](https://pyyaml.org/) - YAML file handling
- [GraphRAG Accelerator](https://github.com/Azure-Samples/graphrag-accelerator) - Graph-based code analysis patterns and implementation concepts

## Disclaimer

This project is not an officially supported product. It is provided as-is, without warranty or support. Users should evaluate its suitability for their use case and understand the implications of deep code analysis on their systems.

## How to Get Help

- For bugs and feature requests, please [open an issue](https://github.com/mikewcasale/repominify/issues)
- For usage questions, please [start a discussion](https://github.com/mikewcasale/repominify/discussions)
- For security concerns, please email security@casale.xyz directly

## Trademarks

Any trademarks or registered trademarks mentioned in this project are the property of their respective owners.

