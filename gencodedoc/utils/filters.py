"""File filtering utilities"""
import pathspec
from pathlib import Path
from typing import List

class FileFilter:
    """Handles file/directory filtering"""

    def __init__(self, ignore_config, project_root: Path):
        """
        Initialize filter

        Args:
            ignore_config: IgnoreConfig instance
            project_root: Project root path
        """
        self.ignore_config = ignore_config
        self.project_root = project_root

        # Create pathspec for gitignore-style patterns
        self.pathspec = pathspec.PathSpec.from_lines(
            'gitwildmatch',
            ignore_config.patterns
        )

    def should_ignore(self, path: Path, is_directory: bool = False) -> bool:
        """Check if path should be ignored"""
        name = path.name

        # Check directory ignore list
        if is_directory and name in self.ignore_config.dirs:
            return True

        # Check file ignore list
        if not is_directory and name in self.ignore_config.files:
            return True

        # Check extension ignore list
        if not is_directory:
            ext = path.suffix.lower()
            if ext in self.ignore_config.extensions:
                return True

        # Check patterns
        try:
            relative_path = path.relative_to(self.project_root)
            if self.pathspec.match_file(str(relative_path)):
                return True
        except ValueError:
            pass

        return False

    def filter_paths(self, paths: List[Path]) -> List[Path]:
        """Filter list of paths"""
        return [
            p for p in paths
            if not self.should_ignore(p, p.is_dir())
        ]

    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Path]:
        """Scan directory and return filtered file list"""
        files = []

        try:
            for item in directory.iterdir():
                if self.should_ignore(item, item.is_dir()):
                    continue

                if item.is_file():
                    files.append(item)
                elif item.is_dir() and recursive:
                    files.extend(self.scan_directory(item, recursive))
        except PermissionError:
            pass

        return files


class BinaryDetector:
    """Detect if file is binary"""

    TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})

    @staticmethod
    def is_binary(file_path: Path, chunk_size: int = 8192) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(chunk_size)
                if not chunk:
                    return False

                # Check for null bytes
                if b'\x00' in chunk:
                    return True

                # Check ratio of text characters
                non_text = chunk.translate(None, BinaryDetector.TEXT_CHARS)
                return len(non_text) / len(chunk) > 0.3
        except Exception:
            return True
