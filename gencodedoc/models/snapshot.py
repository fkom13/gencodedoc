"""Snapshot data models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import fnmatch

class FileEntry(BaseModel):
    """Single file in a snapshot"""
    path: str
    hash: str
    size: int
    mode: int = 0o644

class SnapshotMetadata(BaseModel):
    """Snapshot metadata"""
    id: Optional[int] = None
    hash: str = ""
    message: Optional[str] = None
    tag: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    parent_id: Optional[int] = None
    is_autosave: bool = False
    trigger_type: str = 'manual'
    files_count: int = 0
    total_size: int = 0
    compressed_size: int = 0

class Snapshot(BaseModel):
    """Complete snapshot"""
    metadata: SnapshotMetadata
    files: List[FileEntry] = Field(default_factory=list)

    def get_file(self, path: str) -> Optional[FileEntry]:
        """Get a specific file entry by path"""
        for f in self.files:
            if f.path == path:
                return f
        return None

    def get_files_matching(self, patterns: List[str]) -> List[FileEntry]:
        """Get files matching glob patterns or path prefixes"""
        matched = []
        for f in self.files:
            for pattern in patterns:
                if fnmatch.fnmatch(f.path, pattern) or f.path.startswith(pattern):
                    matched.append(f)
                    break
        return matched

class DiffEntry(BaseModel):
    """Single file diff"""
    file_path: str
    status: str  # added, removed, modified, renamed
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    diff_content: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0

class SnapshotDiff(BaseModel):
    """Diff between snapshots"""
    from_snapshot: int = 0
    to_snapshot: int = 0
    files_added: List[str] = Field(default_factory=list)
    files_removed: List[str] = Field(default_factory=list)
    files_modified: List[DiffEntry] = Field(default_factory=list)
    files_renamed: List[Dict[str, str]] = Field(default_factory=list)
    total_changes: int = 0
    significance_score: float = 0.0

    def filter_by_paths(self, paths: List[str]) -> 'SnapshotDiff':
        """Return a new SnapshotDiff filtered to only include specified paths"""
        def matches(file_path: str) -> bool:
            for pattern in paths:
                if fnmatch.fnmatch(file_path, pattern):
                    return True
                if file_path.startswith(pattern):
                    return True
                if file_path == pattern:
                    return True
            return False

        filtered = SnapshotDiff(
            from_snapshot=self.from_snapshot,
            to_snapshot=self.to_snapshot,
            files_added=[p for p in self.files_added if matches(p)],
            files_removed=[p for p in self.files_removed if matches(p)],
            files_modified=[e for e in self.files_modified if matches(e.file_path)],
            files_renamed=[r for r in self.files_renamed if matches(r.get('from', '')) or matches(r.get('to', ''))],
        )
        filtered.total_changes = (
            len(filtered.files_added) +
            len(filtered.files_removed) +
            len(filtered.files_modified)
        )
        total = max(self.total_changes, 1)
        filtered.significance_score = filtered.total_changes / total
        return filtered

