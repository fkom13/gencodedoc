"""File scanning functionality"""
import hashlib
from pathlib import Path
from typing import List, Optional
from ..models.snapshot import FileEntry
from ..models.config import ProjectConfig
from ..utils.filters import FileFilter, BinaryDetector

class FileScanner:
    """Scans project files with filtering"""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.filter = FileFilter(config.ignore, config.project_path)
        self.binary_detector = BinaryDetector()

    def scan(
        self,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        include_binary: bool = False
    ) -> List[FileEntry]:
        """Scan project files"""
        if include_paths:
            files = self._scan_specific_paths(include_paths)
        else:
            files = self.filter.scan_directory(self.config.project_path)

        if exclude_paths:
            exclude_set = {self.config.project_path / p for p in exclude_paths}
            files = [f for f in files if f not in exclude_set]

        if not include_binary:
            files = [f for f in files if not self.binary_detector.is_binary(f)]

        return self._create_file_entries(files)

    def _scan_specific_paths(self, paths: List[str]) -> List[Path]:
        """Scan specific paths"""
        files = []

        for path_str in paths:
            path = self.config.project_path / path_str

            if not path.exists():
                continue

            if path.is_file():
                if not self.filter.should_ignore(path, False):
                    files.append(path)
            elif path.is_dir():
                files.extend(self.filter.scan_directory(path))

        return files

    def _create_file_entries(self, files: List[Path]) -> List[FileEntry]:
        """Convert Path to FileEntry"""
        entries = []

        for file_path in files:
            try:
                file_hash = self._calculate_file_hash(file_path)
                stat = file_path.stat()

                try:
                    relative_path = file_path.relative_to(self.config.project_path)
                except ValueError:
                    relative_path = file_path

                entry = FileEntry(
                    path=str(relative_path),
                    hash=file_hash,
                    size=stat.st_size,
                    mode=stat.st_mode
                )
                entries.append(entry)

            except Exception as e:
                print(f"Warning: Could not process {file_path}: {e}")
                continue

        return entries

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA256 hash"""
        hasher = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)

        return hasher.hexdigest()
