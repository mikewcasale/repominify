"""Custom exceptions for repo-minify.

This module contains all custom exceptions used throughout the codebase.
"""

from __future__ import annotations


class GraphBuildError(Exception):
    """Base exception for graph building errors.

    Raises:
        GraphBuildError: When graph construction fails

    Examples::
        >>> try:
        ...     raise GraphBuildError("Failed to build graph")
        ... except GraphBuildError as e:
        ...     str(e)
        'Failed to build graph'
    """

    pass


class FileParseError(GraphBuildError):
    """Raised when Repomix file parsing fails.

    Raises:
        FileParseError: When file parsing fails

    Examples::
        >>> try:
        ...     raise FileParseError("Invalid file format")
        ... except FileParseError as e:
        ...     str(e)
        'Invalid file format'
    """

    pass


class ValidationError(GraphBuildError):
    """Raised when input validation fails.

    Raises:
        ValidationError: When input validation fails

    Examples::
        >>> try:
        ...     raise ValidationError("Invalid input")
        ... except ValidationError as e:
        ...     str(e)
        'Invalid input'
    """

    pass


class DependencyError(Exception):
    """Base exception for dependency-related errors.

    Raises:
        DependencyError: When dependency management fails

    Examples::
        >>> try:
        ...     raise DependencyError("Missing dependency")
        ... except DependencyError as e:
        ...     str(e)
        'Missing dependency'
    """

    pass


class CommandExecutionError(DependencyError):
    """Raised when a system command fails.

    Raises:
        CommandExecutionError: When command execution fails

    Examples::
        >>> try:
        ...     raise CommandExecutionError("Command failed")
        ... except CommandExecutionError as e:
        ...     str(e)
        'Command failed'
    """

    pass


class InstallationError(DependencyError):
    """Raised when package installation fails.

    Raises:
        InstallationError: When package installation fails

    Examples::
        >>> try:
        ...     raise InstallationError("Installation failed")
        ... except InstallationError as e:
        ...     str(e)
        'Installation failed'
    """

    pass
