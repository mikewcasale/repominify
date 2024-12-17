"""Logging configuration for repo-minify.

This module provides consistent logging configuration across the package.
"""

import logging
import sys
from typing import Optional

from .types import LogLevel


def configure_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging for repo-minify.

    Args:
        debug: Enable debug level logging
        log_file: Optional file path for logging output

    Raises:
        OSError: If log file cannot be created or written to
        ValueError: If log file path is invalid

    Examples::
        >>> configure_logging(debug=True)
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
        DEBUG: Debug message
    """
    root_logger = logging.getLogger("repo_minify")
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create formatters
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Examples::
        >>> logger = get_logger(__name__)
        >>> isinstance(logger, logging.Logger)
        True
        >>> logger.name.startswith('repo_minify.')
        True
    """
    return logging.getLogger(f"repo_minify.{name}")


# Default logger for this module
logger = get_logger(__name__)
