"""Snapshot storage management"""
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import Database
from .compression import Compressor
from ..models.snapshot import Snapshot, SnapshotMetadata, FileEntry


class SnapshotStore:
    """Manages snapshot storage and retrieval"""

    def __init__(self, storage_path: Path, project_path: Path, compression_level: int = 3):
        self.storage_path = storage_path
        self.project_path = project_path  # ✅ NOUVEAU
        import sys
        print(f"🔍 SnapshotStore DEBUG:", file=sys.stderr)
        print(f"  - storage_path: {storage_path}", file=sys.stderr)
        print(f"  - project_path: {project_path}", file=sys.stderr)
        print(f"  - DB: {storage_path / 'gencodedoc.db'}", file=sys.stderr)
        sys.stderr.flush()
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
                # Read and compress file - utiliser chemin ABSOLU
                file_path = self.project_path / file_entry.path  # ✅ ABSOLU
                if file_path.exists():
                    compressed, orig_size, comp_size = self.compressor.compress_file(
                        str(file_path)
                    )
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
