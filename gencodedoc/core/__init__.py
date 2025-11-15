"""Core functionality"""
from .config import ConfigManager
from .scanner import FileScanner
from .versioning import VersionManager
from .documentation import DocumentationGenerator
from .differ import DiffGenerator
from .autosave import AutosaveManager

__all__ = [
    "ConfigManager",
    "FileScanner",
    "VersionManager",
    "DocumentationGenerator",
    "DiffGenerator",
    "AutosaveManager",
]
