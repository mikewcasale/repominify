"""
repominify - Optimize codebase representations for LLMs

Author: Mike Casale
Email: mike@casale.xyz
GitHub: https://github.com/mikewcasale
"""

__version__ = "0.1.6"
__author__ = "Mike Casale"
__email__ = "mike@casale.xyz"

from .graph import CodeGraphBuilder
from .dependencies import ensure_dependencies
from .logging import configure_logging

__all__ = ["CodeGraphBuilder", "ensure_dependencies", "configure_logging"]
