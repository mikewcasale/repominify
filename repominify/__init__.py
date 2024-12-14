"""
repominify - Optimize codebase representations for LLMs
"""

__version__ = "0.1.3"
__author__ = "Mike Casale"
__email__ = "mike@casale.xyz"

from .core.graph import CodeGraphBuilder
from .utils.dependency_checker import ensure_dependencies
from .utils.logging import configure_logging

__all__ = ["CodeGraphBuilder", "ensure_dependencies", "configure_logging"]
