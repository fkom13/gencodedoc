"""
gencodedoc - Smart documentation generator and intelligent versioning system
"""

__version__ = "2.1.0"
__author__ = "Your Name"
__license__ = "MIT"

import os
import logging

# Configure logging based on GENCODEDOC_DEBUG
log_level = logging.DEBUG if os.environ.get("GENCODEDOC_DEBUG") else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
