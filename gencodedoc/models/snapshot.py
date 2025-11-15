"""Snapshot data models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class FileEntry(BaseModel):
    """Single file in a snapshot"""
    path: str
    hash: str
    size: int
    mode: int = 0o644

class SnapshotMetadata(BaseModel):
    """Snapshot metadata"""
    id: Optional[int] = None
    hash: str
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
    from_snapshot: int
    to_snapshot: int
    files_added: List[str] = Field(default_factory=list)
    files_removed: List[str] = Field(default_factory=list)
    files_modified: List[DiffEntry] = Field(default_factory=list)
    files_renamed: List[Dict[str, str]] = Field(default_factory=list)
    total_changes: int = 0
    significance_score: float = 0.0
