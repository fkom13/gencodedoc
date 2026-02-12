# gencodedoc (Partie 4)
> Suite de la documentation (12/02/2026)

### 📄 `gencodedoc/storage/snapshot_store.py`

```python
"""Snapshot storage management"""
import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import Database
from .compression import Compressor
from ..models.snapshot import Snapshot, SnapshotMetadata, FileEntry

logger = logging.getLogger(__name__)


class SnapshotStore:
    """Manages snapshot storage and retrieval"""

    def __init__(self, storage_path: Path, project_path: Path, compression_level: int = 3, compression_enabled: bool = True):
        self.storage_path = storage_path
        self.project_path = project_path
        self.compression_enabled = compression_enabled
        logger.debug(f"SnapshotStore init: storage={storage_path}, project={project_path}, compression={'ON' if compression_enabled else 'OFF'}")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.db = Database(storage_path / "gencodedoc.db")
        self.compressor = Compressor(level=compression_level)

    def create_snapshot(
        self,
        files: List[FileEntry],
        message: Optional[str] = None,
        tag: Optional[str] = None,
        is_autosave: bool = False,
        trigger_type: str = 'manual'
    ) -> Snapshot:
        """
        Create new snapshot

        Args:
            files: List of file entries
            message: Optional message
            tag: Optional tag for easy reference
            is_autosave: Whether this is an autosave
            trigger_type: What triggered the snapshot

        Returns:
            Created snapshot
        """
        # Calculate snapshot hash
        snapshot_hash = self._calculate_snapshot_hash(files)

        # Get parent (latest snapshot)
        latest = self.db.get_latest_snapshot()
        parent_id = latest['id'] if latest else None

        # Calculate sizes
        total_size = sum(f.size for f in files)

        # Create snapshot record
        snapshot_id = self.db.create_snapshot(
            hash=snapshot_hash,
            message=message,
            tag=tag,
            is_autosave=is_autosave,
            trigger_type=trigger_type,
            parent_id=parent_id,
            files_count=len(files),
            total_size=total_size,
            compressed_size=0  # Will update after storing files
        )

        # Store file contents
        total_compressed = 0
        for file_entry in files:
            # Add file to snapshot
            self.db.add_file_to_snapshot(
                snapshot_id=snapshot_id,
                file_path=file_entry.path,
                file_hash=file_entry.hash,
                size=file_entry.size,
                mode=file_entry.mode
            )

            # Store content if not already stored (deduplication)
            if not self.db.content_exists(file_entry.hash):
                # Read file
                file_path = self.project_path / file_entry.path
                if file_path.exists():
                    if self.compression_enabled:
                        compressed, orig_size, comp_size = self.compressor.compress_file(str(file_path))
                    else:
                        # Store raw content
                        content = file_path.read_bytes()
                        compressed = content
                        orig_size = len(content)
                        comp_size = orig_size
                    
                    total_compressed += comp_size

                    # Store in database
                    self.db.store_content(
                        content_hash=file_entry.hash,
                        content=compressed,
                        original_size=orig_size,
                        compressed_size=comp_size
                    )

        # Create metadata
        metadata = SnapshotMetadata(
            id=snapshot_id,
            hash=snapshot_hash,
            message=message,
            tag=tag,
            created_at=datetime.now(),
            parent_id=parent_id,
            is_autosave=is_autosave,
            trigger_type=trigger_type,
            files_count=len(files),
            total_size=total_size,
            compressed_size=total_compressed
        )

        return Snapshot(metadata=metadata, files=files)

    def get_snapshot(self, snapshot_id: int) -> Optional[Snapshot]:
        """Get snapshot by ID"""
        snapshot_data = self.db.get_snapshot(snapshot_id)
        if not snapshot_data:
            return None

        # Get files
        files_data = self.db.get_snapshot_files(snapshot_id)
        files = [
            FileEntry(
                path=f['file_path'],
                hash=f['file_hash'],
                size=f['size'],
                mode=f['mode']
            )
            for f in files_data
        ]

        # Create metadata
        metadata = SnapshotMetadata(**snapshot_data)

        return Snapshot(metadata=metadata, files=files)

    def get_snapshot_by_tag(self, tag: str) -> Optional[Snapshot]:
        """Get snapshot by tag"""
        snapshot_data = self.db.get_snapshot_by_tag(tag)
        if not snapshot_data:
            return None
        return self.get_snapshot(snapshot_data['id'])

    def list_snapshots(
        self,
        limit: Optional[int] = None,
        include_autosave: bool = True
    ) -> List[SnapshotMetadata]:
        """List all snapshots"""
        snapshots_data = self.db.list_snapshots(limit, include_autosave)
        return [SnapshotMetadata(**s) for s in snapshots_data]

    def restore_file(self, file_hash: str, target_path: Path) -> bool:
        """
        Restore single file from snapshot

        Args:
            file_hash: Hash of file to restore
            target_path: Where to write the file

        Returns:
            True if successful
        """
        content = self.db.get_content(file_hash)
        if not content:
            return False

        # Decompress
        decompressed = self.compressor.decompress(content)

        # Write file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(decompressed)

        return True

    def restore_snapshot(
        self,
        snapshot_id: int,
        target_dir: Path,
        force: bool = False
    ) -> bool:
        """
        Restore entire snapshot

        Args:
            snapshot_id: Snapshot to restore
            target_dir: Directory to restore to
            force: Overwrite existing files

        Returns:
            True if successful
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            return False

        for file_entry in snapshot.files:
            target_path = target_dir / file_entry.path

            # Check if file exists
            if target_path.exists() and not force:
                raise FileExistsError(
                    f"File {target_path} already exists. Use --force to overwrite."
                )

            # Restore file
            if not self.restore_file(file_entry.hash, target_path):
                return False

            # Restore permissions
            target_path.chmod(file_entry.mode)

        return True

    def get_file_content(self, file_hash: str) -> Optional[str]:
        """
        Get decompressed file content as string

        Args:
            file_hash: Hash of file content

        Returns:
            File content as string, or None if not found
        """
        content = self.db.get_content(file_hash)
        if not content:
            return None
        try:
            decompressed = self.compressor.decompress(content)
            return decompressed.decode('utf-8')
        except (UnicodeDecodeError, Exception):
            return None

    def get_file_content_bytes(self, file_hash: str) -> Optional[bytes]:
        """
        Get decompressed file content as bytes

        Args:
            file_hash: Hash of file content

        Returns:
            File content as bytes, or None if not found
        """
        content = self.db.get_content(file_hash)
        if not content:
            return None
        try:
            return self.compressor.decompress(content)
        except Exception:
            return None

    def delete_snapshot(self, snapshot_id: int) -> None:
        """Delete snapshot"""
        self.db.delete_snapshot(snapshot_id)

    def cleanup_old_autosaves(self, max_keep: int = 50) -> int:
        """Clean up old autosaves"""
        return self.db.cleanup_old_autosaves(max_keep)

    @staticmethod
    def _calculate_snapshot_hash(files: List[FileEntry]) -> str:
        """Calculate unique hash for snapshot"""
        hasher = hashlib.sha256()

        # Sort files for consistent hashing
        sorted_files = sorted(files, key=lambda f: f.path)

        for file_entry in sorted_files:
            hasher.update(file_entry.path.encode())
            hasher.update(file_entry.hash.encode())

        return hasher.hexdigest()

```

### 📄 `gencodedoc/utils/__init__.py`

```python
"""Utility functions"""
from .filters import FileFilter, BinaryDetector
from .formatters import format_size, format_date, get_language_from_extension
from .tree import TreeGenerator

__all__ = [
    "FileFilter",
    "BinaryDetector",
    "format_size",
    "format_date",
    "get_language_from_extension",
    "TreeGenerator"
]

```

### 📄 `gencodedoc/utils/filters.py`

```python
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

    def scan_directory(self, directory: Path, recursive: bool = True):
        """Scan directory and yield filtered files (generator)"""
        try:
            for item in directory.iterdir():
                if self.should_ignore(item, item.is_dir()):
                    continue

                if item.is_file():
                    yield item
                elif item.is_dir() and recursive:
                    yield from self.scan_directory(item, recursive)
        except PermissionError:
            pass


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

```

### 📄 `gencodedoc/utils/formatters.py`

```python
"""Formatting utilities"""
from datetime import datetime
from typing import Union

def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_date(dt: Union[datetime, str], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(fmt)


def get_language_from_extension(file_path: str) -> str:
    """Get language identifier for syntax highlighting"""
    import os
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'jsx',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.md': 'markdown',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.sql': 'sql',
        '.r': 'r',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.dart': 'dart',
    }

    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path).lower()

    if filename == 'dockerfile':
        return 'dockerfile'
    if filename == 'makefile':
        return 'makefile'

    return ext_map.get(ext, 'text')

```

### 📄 `gencodedoc/utils/tree.py`

```python
"""Directory tree generation"""
from pathlib import Path
from typing import Optional, Set, Callable

class TreeGenerator:
    """Generate directory tree visualization"""

    def __init__(self, show_hidden: bool = False):
        self.show_hidden = show_hidden

    def generate(
        self,
        root: Path,
        prefix: str = '',
        is_last: bool = True,
        max_depth: Optional[int] = None,
        current_depth: int = 0,
        filter_func: Optional[Callable] = None,
        paginate: bool = False,
        page: int = 1,
        limit: int = 50
    ) -> str:
        """Generate tree structure string (optionally paginated)"""
        if paginate:
            all_lines = self.generate_lines(root, prefix, is_last, max_depth, current_depth, filter_func)
            total_lines = len(all_lines)
            start = (page - 1) * limit
            end = start + limit
            
            page_lines = all_lines[start:end]
            
            if not page_lines:
                return f"(Page {page} empty - Total lines: {total_lines})"
            
            header = []
            if page > 1:
                header = [f"... (lines 1-{start} hidden) ..."]
                
            footer = []
            if end < total_lines:
                footer = [f"... ({total_lines - end} more lines) ..."]
                
            return "\n".join(header + page_lines + footer)
        else:
            return "\n".join(self.generate_lines(root, prefix, is_last, max_depth, current_depth, filter_func))

    def generate_lines(
        self,
        root: Path,
        prefix: str = '',
        is_last: bool = True,
        max_depth: Optional[int] = None,
        current_depth: int = 0,
        filter_func: Optional[Callable] = None
    ) -> list[str]:
        """Generate list of tree lines"""
        if max_depth is not None and current_depth >= max_depth:
            return []

        lines = []
        basename = root.name

        if current_depth == 0:
            lines.append(f"{basename}")
        else:
            connector = '└── ' if is_last else '├── '
            lines.append(f"{prefix}{connector}{basename}")

        try:
            items = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            if not self.show_hidden:
                items = [i for i in items if not i.name.startswith('.')]

            if filter_func:
                items = [i for i in items if filter_func(i)]

            for index, item in enumerate(items):
                is_last_item = index == len(items) - 1

                if current_depth == 0:
                    new_prefix = ''
                else:
                    new_prefix = prefix + ('    ' if is_last else '│   ')

                if item.is_dir():
                    lines.extend(self.generate_lines(
                        item,
                        new_prefix,
                        is_last_item,
                        max_depth,
                        current_depth + 1,
                        filter_func
                    ))
                else:
                    connector = '└── ' if is_last_item else '├── '
                    lines.append(f"{new_prefix}{connector}{item.name}")

        except PermissionError:
            pass

        return lines

    def generate_with_selection(
        self,
        root: Path,
        selected_paths: Set[Path],
        filter_func: Optional[Callable] = None
    ) -> str:
        """Generate tree showing all structure but marking selected files"""
        return self._generate_marked(root, selected_paths, '', True, filter_func)

    def _generate_marked(
        self,
        root: Path,
        selected: Set[Path],
        prefix: str,
        is_last: bool,
        filter_func: Optional[Callable]
    ) -> str:
        """Internal method for marked tree generation"""
        tree = ''
        basename = root.name

        marker = ' ✓' if root in selected else ''

        if prefix == '':
            tree += f"{basename}{marker}\n"
        else:
            tree += prefix + ('└── ' if is_last else '├── ') + basename + marker + '\n'

        try:
            items = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            if not self.show_hidden:
                items = [i for i in items if not i.name.startswith('.')]

            if filter_func:
                items = [i for i in items if filter_func(i)]

            for index, item in enumerate(items):
                is_last_item = index == len(items) - 1
                new_prefix = prefix + ('    ' if is_last else '│   ')

                if item.is_dir():
                    tree += self._generate_marked(
                        item, selected, new_prefix, is_last_item, filter_func
                    )
                else:
                    marker = ' ✓' if item in selected else ''
                    tree += new_prefix + ('└── ' if is_last_item else '├── ') + item.name + marker + '\n'

        except PermissionError:
            pass

        return tree

```

### 📄 `pyproject.toml`

```toml
[tool.poetry]
name = "gencodedoc"
version = "2.4.0"
description = "Smart documentation generator and intelligent versioning system with MCP support"
authors = ["fkom13 <fkom13@esprit-artificiel.com>"]
readme = "README.md"
license = "MIT"
homepage = "https://github.com/fkom13/gencodedoc"
repository = "https://github.com/fkom13/gencodedoc"
keywords = ["documentation", "versioning", "mcp", "snapshot", "diff", "ai-tools"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Documentation",
    "Topic :: Software Development :: Version Control",
]

[tool.poetry.dependencies]
python = "^3.10"
typer = {extras = ["all"], version = "^0.20.0"}
rich = "^13.7.0"
pydantic = "^2.5.0"
pyyaml = "^6.0.1"
pathspec = "^0.11.2"
zstandard = "^0.22.0"
watchdog = "^3.0.0"
fastapi = "^0.121.0"
uvicorn = "^0.38.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.1"
black = "^23.12.1"
ruff = "^0.1.8"
mypy = "^1.7.1"

[tool.poetry.scripts]
gencodedoc = "gencodedoc.cli.main:app"
gcd = "gencodedoc.cli.main:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true

```

### 📄 `rsync_sync.sh`

```bash
#!/bin/bash
set -e

SOURCE_DIR="/home/fkomp/Bureau/oracle/utilitaires/gencodedoc/gencodedoc/"
DEST_DIR="/home/fkomp/Bureau/oracle/tools/_Publies/gencodedoc/"

echo "🚀 Syncing from Source to GitHub-ready..."

# Sync source code (gencodedoc package)
rsync -av --delete \
  --exclude='__pycache__' \
  --exclude='.gencodedoc' \
  --exclude='.gencodedoc.yaml' \
  --exclude='.gencodedoc.example.yaml' \
  --exclude='poetry.lock' \
  --exclude='Audit_General_Complet.md' \
  "$SOURCE_DIR/gencodedoc/" \
  "$DEST_DIR/gencodedoc/"

# Sync other files (Makefile, config presets, tests, etc.)
# Note: config/ is inside gencodedoc/ now, so we sync specific root files and tests if they exist
rsync -av \
  --exclude='__pycache__' \
  --exclude='.gencodedoc*' \
  --exclude='poetry.lock' \
  --exclude='Audit_General_Complet.md' \
  --exclude='README.md' \
  --exclude='pyproject.toml' \
  "$SOURCE_DIR/Makefile" \
  "$SOURCE_DIR/LICENSE" \
  "$SOURCE_DIR/tests" \
  "$DEST_DIR"

echo "✅ Sync complete!"

```



---
**✅ Fin de la documentation.**