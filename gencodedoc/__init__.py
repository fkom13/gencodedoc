"""
gencodedoc - Smart documentation generator and intelligent versioning system
"""

__version__ = "2.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from .core.config import ConfigManager
from .core.scanner import FileScanner
from .core.versioning import VersionManager
from .core.documentation import DocumentationGenerator

__all__ = [
    "ConfigManager",
    "FileScanner",
    "VersionManager",
    "DocumentationGenerator",
]
