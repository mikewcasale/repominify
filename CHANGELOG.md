# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2024-12-14

### Added
- Enhanced code context extraction:
  - Function and method signatures with full parameter lists
  - Complete docstrings with parameter descriptions
  - Constants and their values
  - Environment variables and configurations
  - Module-level documentation
  - Import relationships
  - Class hierarchies and dependencies
- Improved text representation format for better LLM context
- More detailed output file documentation

### Fixed
- File count statistics in output file comparison
- More accurate comparison between input and output files

## [0.1.4] - 2024-12-14

### Fixed
- CLI entry point path to use correct module location
- Package structure for proper imports

## [0.1.3] - 2024-12-14

### Changed
- Improved package organization while maintaining repominify name

## [0.1.2] - 2024-12-14

### Fixed
- Package import structure to properly expose modules
- Added package data configuration
- Disabled zip_safe to ensure proper module loading

## [0.1.1] - 2024-12-14

### Fixed
- Package import structure to work with current src/ layout
- CLI entry point path
- Package discovery configuration

## [0.1.0] - 2024-12-14

### Added
- Initial release of repominify
- Core functionality for processing Repomix output
- Graph-based code structure analysis
- Multiple output formats (GraphML, JSON, YAML, Text)
- Automatic dependency management for Node.js and npm
- Size optimization with comparison statistics
- Security pattern detection
- Comprehensive logging and debug support
- Command-line interface and Python API
- End-to-end test suite
- GitHub Actions for automated PyPI publishing

### Changed
- Renamed package from repo-minify to repominify
- Restructured project to use src/ directory layout
- Updated package metadata and documentation

[0.1.5]: https://github.com/mikewcasale/repominify/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/mikewcasale/repominify/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/mikewcasale/repominify/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/mikewcasale/repominify/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/mikewcasale/repominify/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/mikewcasale/repominify/releases/tag/v0.1.0 